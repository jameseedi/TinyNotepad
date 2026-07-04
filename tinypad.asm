; tinypad.asm — a usable Win32 notepad in well under 2048 bytes
;
; build:  fasm tinypad.asm tinypad.exe
; usage:  tinypad.exe [file]     Ctrl+S saves (to [file], or tinypad.txt)
;
; The whole file is a hand-crafted PE32 in "low alignment" mode
; (SectionAlignment = FileAlignment = 4), so file offsets == RVAs and the
; image is mapped as-is. The DOS and PE headers overlap: e_lfanew = 4, which
; places the PE header at offset 4 and makes the dword at file offset 0x3C
; serve simultaneously as e_lfanew (must be 4) and SectionAlignment (must
; be 4). Unused-by-the-loader header fields double as data storage:
;   - COFF TimeDateStamp/PointerToSymbolTable/NumberOfSymbols (12 bytes)
;     hold the default save path "tinypad.txt",0
;   - the section Name field (8 bytes) holds the window class "EDIT",0
;
; No RegisterClass, no window procedure: the EDIT control itself is created
; as the top-level window. EDIT forwards unhandled messages to
; DefWindowProc, so WM_CLOSE destroys the window; GetMessageA filtered on
; that hwnd then returns -1 (invalid window) and the loop falls out to
; ExitProcess. WM_SIZE reflow is EDIT's own behaviour — no MoveWindow.
;
; TranslateMessage IS imported (the spec suggested skipping it, but without
; it no WM_KEYDOWN ever becomes WM_CHAR and typing is impossible). It also
; gives us the save hotkey for free: Ctrl+S arrives as WM_CHAR/0x13 and is
; intercepted in the message loop before dispatch.
;
; The 64 KiB text buffer lives on the stack; SizeOfStackCommit = 0x20000
; pre-commits it so no guard-page probing code is needed.

format binary as 'exe'
use32

BASE = 0x400000
org BASE

; ---------------------------------------------------------------- headers
        db      'MZ'                    ; 00  e_magic (rest of DOS header
        dw      0                       ; 02   overlaps the PE header)
        db      'PE',0,0                ; 04  PE signature  (e_lfanew -> 4)
        dw      0x014C                  ; 08  Machine: i386
        dw      1                       ; 0A  NumberOfSections
savepath db     'tinypad.txt',0         ; 0C  TimeDateStamp / PtrSymTable /
                                        ;     NumSymbols: loader ignores all
                                        ;     12 bytes -> default save path
        dw      opt_end - opt           ; 18  SizeOfOptionalHeader
        dw      0x0103                  ; 1A  EXE | RELOCS_STRIPPED | 32BIT
opt:    dw      0x010B                  ; 1C  Magic: PE32
        db      0,0                     ; 1E  linker version (unused)
        dd      0,0,0                   ; 20  SizeOfCode/Init/Uninit (unused)
        dd      start - BASE            ; 2C  AddressOfEntryPoint
        dd      0,0                     ; 30  BaseOfCode/BaseOfData (unused)
        dd      BASE                    ; 38  ImageBase
        dd      4                       ; 3C  SectionAlignment == e_lfanew
        dd      4                       ; 40  FileAlignment
        dw      4,0                     ; 44  OS version 4.0
        dd      0                       ; 48  image version (unused)
        dw      4,0                     ; 4C  subsystem version 4.0
        dd      0                       ; 50  Win32VersionValue (must be 0)
        dd      (filesize+3) and 0xFFFFFFFC ; 54  SizeOfImage
        dd      hdrs_end - BASE         ; 58  SizeOfHeaders
        dd      0                       ; 5C  Checksum (unchecked for exes)
        dw      2                       ; 60  Subsystem: GUI
        dw      0                       ; 62  DllCharacteristics
        dd      0x100000                ; 64  SizeOfStackReserve
        dd      0x20000                 ; 68  SizeOfStackCommit: pre-commits
                                        ;     the 64K stack text buffer
        dd      0x100000                ; 6C  SizeOfHeapReserve
        dd      0                       ; 70  SizeOfHeapCommit
        dd      0                       ; 74  LoaderFlags
        dd      2                       ; 78  NumberOfRvaAndSizes (truncated)
        dd      0,0                     ; 7C  export directory: none
        dd      idata - BASE            ; 84  import directory RVA
        dd      idata_end - idata       ; 88  import directory size
opt_end:
; single section covering everything after the headers, R+W+X
cls_edit db     'EDIT',0,0,0,0          ; 8C  Name -> window class string
        dd      filesize - (hdrs_end-BASE) ; 94  VirtualSize
        dd      hdrs_end - BASE         ; 98  VirtualAddress
        dd      filesize - (hdrs_end-BASE) ; 9C  SizeOfRawData
        dd      hdrs_end - BASE         ; A0  PointerToRawData
        dd      0,0                     ; A4  relocs/linenumbers (none)
        dd      0                       ; AC  their counts (none)
        dd      0xE0000060              ; B0  CODE|INITIALIZED|RWX
hdrs_end:

; ------------------------------------------------------------------- code
start:
        sub     esp, 0x10800
        mov     edi, esp                ; edi -> 64K text buffer (stack)
        sub     esp, 32
        mov     ebp, esp                ; ebp -> MSG, [ebp+28] scratch dword

; path = argv[1] if present else "tinypad.txt" (stashed in the COFF header)
        call    [GetCommandLineA]
        xchg    esi, eax
        lodsb
        cmp     al, '"'
        je      qexe
pexe:   cmp     al, ' '                 ; skip unquoted program name
        jbe     args
        lodsb
        jmp     pexe
qexe:   lodsb                           ; skip quoted program name
        test    al, al
        jz      args
        cmp     al, '"'
        jne     qexe
        lodsb
args:   cmp     al, ' '                 ; skip separating spaces
        jne     got
        lodsb
        jmp     args
got:    dec     esi                     ; esi -> argument (or its NUL)
        cmp     byte [esi], 0
        jne     strip
        mov     esi, savepath
        jmp     mkwnd
strip:  cmp     byte [esi], '"'         ; unquote: drop leading quote and
        jne     mkwnd                   ; overwrite the closing one with NUL
        inc     esi                     ; (the command line buffer returned
        push    esi                     ; by GetCommandLineA is writable)
uq:     lodsb
        test    al, al
        jz      uq2
        cmp     al, '"'
        jne     uq
uq2:    mov     byte [esi-1], 0
        pop     esi

; the editor: one top-level EDIT control, word-wrapped, vertical scrollbar
mkwnd:  xor     eax, eax
        push    eax                     ; lpParam
        push    eax                     ; hInstance (system class)
        push    eax                     ; hMenu
        push    eax                     ; hWndParent
        mov     ecx, 0x80000000         ; CW_USEDEFAULT
        push    ecx                     ; nHeight
        push    ecx                     ; nWidth
        push    ecx                     ; Y
        push    ecx                     ; X
        push    0x10EF0044              ; WS_OVERLAPPEDWINDOW or WS_VISIBLE
                                        ; or WS_VSCROLL or ES_MULTILINE
                                        ; or ES_AUTOVSCROLL
        push    eax                     ; lpWindowName
        push    cls_edit                ; "EDIT" (the section name field)
        push    eax                     ; dwExStyle
        call    [CreateWindowExA]
        xchg    ebx, eax                ; ebx = hwnd

        push    16                      ; SYSTEM_FIXED_FONT (Fixedsys — the
        call    [GetStockObject]        ;  original Notepad look)
        push    1                       ; lParam: redraw
        push    eax                     ; wParam: hFont
        push    0x30                    ; WM_SETFONT
        push    ebx
        call    [SendMessageA]

        push    0
        push    0xFFF0                  ; raise EDIT's default text limit
        push    0xC5                    ; EM_SETLIMITTEXT
        push    ebx
        call    [SendMessageA]

; load-on-launch: if the file exists, read it into the buffer and set text
        xor     eax, eax
        push    eax                     ; hTemplateFile
        push    eax                     ; dwFlagsAndAttributes
        push    3                       ; OPEN_EXISTING
        push    eax                     ; lpSecurityAttributes
        push    1                       ; FILE_SHARE_READ
        push    0x80000000              ; GENERIC_READ
        push    esi
        call    [CreateFileA]
        inc     eax                     ; INVALID_HANDLE_VALUE?
        jz      msgloop
        dec     eax
        push    eax                     ; handle, becomes CloseHandle's arg
        push    0                       ; lpOverlapped
        lea     ecx, [ebp+28]
        push    ecx                     ; lpNumberOfBytesRead
        push    0xFFF0
        push    edi
        push    eax
        call    [ReadFile]
        mov     eax, [ebp+28]
        mov     byte [edi+eax], 0
        push    edi
        push    ebx
        call    [SetWindowTextA]
        call    [CloseHandle]           ; pops the handle pushed above

; message pump, filtered on our hwnd: GetMessageA returns -1 once the
; window is destroyed (WM_CLOSE -> DefWindowProc -> DestroyWindow)
msgloop:
        xor     eax, eax
        push    eax
        push    eax
        push    ebx
        push    ebp
        call    [GetMessageA]
        test    eax, eax
        jle     bye
        cmp     dword [ebp+4], 0x102    ; WM_CHAR ...
        jne     disp
        cmp     dword [ebp+8], 19       ; ... of ^S ?
        je      save
disp:   push    ebp
        call    [TranslateMessage]      ; keydowns -> chars; typing at all
        push    ebp
        call    [DispatchMessageA]
        jmp     msgloop

; Ctrl+S: pull the buffer out of the EDIT and rewrite the file
save:   push    0xFFF0
        push    edi
        push    ebx
        call    [GetWindowTextA]        ; a top-level window's "text" IS the
        push    eax                     ;  EDIT content; returns length
        xor     ecx, ecx
        push    ecx                     ; hTemplateFile
        push    0x80                    ; FILE_ATTRIBUTE_NORMAL
        push    2                       ; CREATE_ALWAYS
        push    ecx                     ; lpSecurityAttributes
        push    ecx                     ; no sharing
        push    0x40000000              ; GENERIC_WRITE
        push    esi
        call    [CreateFileA]
        pop     edx                     ; length
        push    eax                     ; handle, becomes CloseHandle's arg
        push    0                       ; lpOverlapped
        lea     ecx, [ebp+28]
        push    ecx                     ; lpNumberOfBytesWritten
        push    edx
        push    edi
        push    eax
        call    [WriteFile]
        call    [CloseHandle]           ; pops the handle pushed above
        jmp     msgloop

bye:    push    eax
        call    [ExitProcess]

; ---------------------------------------------------------------- imports
; Old-style descriptors: OriginalFirstThunk = 0, so the loader reads the
; hint/name RVAs from the FirstThunk array and overwrites it in place —
; one thunk array instead of two.
align 4
idata:
        dd      0, 0, 0                 ; OFT, TimeDateStamp, ForwarderChain
        dd      n_k32 - BASE
        dd      iat_k32 - BASE
        dd      0, 0, 0
        dd      n_u32 - BASE
        dd      iat_u32 - BASE
        dd      0, 0, 0
        dd      n_g32 - BASE
        dd      iat_g32 - BASE
        dd      0, 0, 0, 0, 0           ; terminator
idata_end:

iat_k32:
GetCommandLineA  dd i_GetCommandLineA - BASE
CreateFileA      dd i_CreateFileA - BASE
ReadFile         dd i_ReadFile - BASE
WriteFile        dd i_WriteFile - BASE
CloseHandle      dd i_CloseHandle - BASE
ExitProcess      dd i_ExitProcess - BASE
        dd      0
iat_u32:
CreateWindowExA  dd i_CreateWindowExA - BASE
SendMessageA     dd i_SendMessageA - BASE
GetMessageA      dd i_GetMessageA - BASE
TranslateMessage dd i_TranslateMessage - BASE
DispatchMessageA dd i_DispatchMessageA - BASE
GetWindowTextA   dd i_GetWindowTextA - BASE
SetWindowTextA   dd i_SetWindowTextA - BASE
        dd      0
iat_g32:
GetStockObject   dd i_GetStockObject - BASE
        dd      0

n_k32:  db      'kernel32.dll',0
n_u32:  db      'user32.dll',0
n_g32:  db      'gdi32.dll',0

i_GetCommandLineA  dw 0
        db      'GetCommandLineA',0
i_CreateFileA      dw 0
        db      'CreateFileA',0
i_ReadFile         dw 0
        db      'ReadFile',0
i_WriteFile        dw 0
        db      'WriteFile',0
i_CloseHandle      dw 0
        db      'CloseHandle',0
i_ExitProcess      dw 0
        db      'ExitProcess',0
i_CreateWindowExA  dw 0
        db      'CreateWindowExA',0
i_SendMessageA     dw 0
        db      'SendMessageA',0
i_GetMessageA      dw 0
        db      'GetMessageA',0
i_TranslateMessage dw 0
        db      'TranslateMessage',0
i_DispatchMessageA dw 0
        db      'DispatchMessageA',0
i_GetWindowTextA   dw 0
        db      'GetWindowTextA',0
i_SetWindowTextA   dw 0
        db      'SetWindowTextA',0
i_GetStockObject   dw 0
        db      'GetStockObject',0

filesize = $ - BASE
