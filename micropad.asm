; micropad.asm — the size-floor variant of tinypad: how small does a
; usable "window + typing + Ctrl+S" editor go?
;
; build:  fasm micropad.asm micropad.exe
; usage:  micropad.exe          Ctrl+S dumps the buffer to tinypad.txt
;
; Same construction as tinypad.asm (see there for the full commentary):
; low-alignment PE32, DOS/PE headers overlapped via e_lfanew = 4, header
; scratch fields reused as string storage, old-style single-thunk imports,
; top-level EDIT control as the only window.
;
; Relative to tinypad.asm this drops: load-on-launch (ReadFile,
; SetWindowTextA), argv[1] handling (GetCommandLineA + parsing), the font
; fix (gdi32 + SendMessageA) and EM_SETLIMITTEXT. Save is the spec's
; cheapest candidate — hotkey to a fixed path.

format binary as 'exe'
use32

BASE = 0x400000
org BASE

; ---------------------------------------------------------------- headers
        db      'MZ'                    ; 00  e_magic
        dw      0                       ; 02
        db      'PE',0,0                ; 04  PE signature  (e_lfanew -> 4)
        dw      0x014C                  ; 08  Machine: i386
        dw      1                       ; 0A  NumberOfSections
savepath db     'tinypad.txt',0         ; 0C  TimeDateStamp / PtrSymTable /
                                        ;     NumSymbols hold the save path
        dw      opt_end - opt           ; 18  SizeOfOptionalHeader
        dw      0x0103                  ; 1A  EXE | RELOCS_STRIPPED | 32BIT
opt:    dw      0x010B                  ; 1C  Magic: PE32
        db      0,0                     ; 1E
        dd      0,0,0                   ; 20  (unused)
        dd      start - BASE            ; 2C  AddressOfEntryPoint
        dd      0,0                     ; 30  (unused)
        dd      BASE                    ; 38  ImageBase
        dd      4                       ; 3C  SectionAlignment == e_lfanew
        dd      4                       ; 40  FileAlignment
        dw      4,0                     ; 44  OS version 4.0
        dd      0                       ; 48  (unused)
        dw      4,0                     ; 4C  subsystem version 4.0
        dd      0                       ; 50  Win32VersionValue (must be 0)
        dd      (filesize+3) and 0xFFFFFFFC ; 54  SizeOfImage
        dd      hdrs_end - BASE         ; 58  SizeOfHeaders
        dd      0                       ; 5C  Checksum
        dw      2                       ; 60  Subsystem: GUI
        dw      0                       ; 62  DllCharacteristics
        dd      0x100000                ; 64  SizeOfStackReserve
        dd      0x20000                 ; 68  SizeOfStackCommit: pre-commits
                                        ;     the 64K stack text buffer
        dd      0x100000                ; 6C  SizeOfHeapReserve
        dd      0                       ; 70  SizeOfHeapCommit
        dd      0                       ; 74  LoaderFlags
        dd      2                       ; 78  NumberOfRvaAndSizes
        dd      0,0                     ; 7C  export directory: none
        dd      idata - BASE            ; 84  import directory RVA
        dd      idata_end - idata       ; 88  import directory size
opt_end:
cls_edit db     'EDIT',0,0,0,0          ; 8C  section Name -> class string
        dd      filesize - (hdrs_end-BASE) ; 94  VirtualSize
        dd      hdrs_end - BASE         ; 98  VirtualAddress
        dd      filesize - (hdrs_end-BASE) ; 9C  SizeOfRawData
        dd      hdrs_end - BASE         ; A0  PointerToRawData
        dd      0,0                     ; A4  relocs/linenumbers
        dd      0                       ; AC  their counts
        dd      0xE0000060              ; B0  CODE|INITIALIZED|RWX
hdrs_end:

; ------------------------------------------------------------------- code
start:
        sub     esp, 0x10800
        mov     edi, esp                ; edi -> 64K text buffer (stack)
        sub     esp, 32
        mov     ebp, esp                ; ebp -> MSG, [ebp+28] scratch dword

        xor     eax, eax
        push    eax                     ; lpParam
        push    eax                     ; hInstance
        push    eax                     ; hMenu
        push    eax                     ; hWndParent
        mov     ecx, 0x80000000         ; CW_USEDEFAULT
        push    ecx
        push    ecx
        push    ecx
        push    ecx
        push    0x10EF0044              ; WS_OVERLAPPEDWINDOW or WS_VISIBLE
                                        ; or WS_VSCROLL or ES_MULTILINE
                                        ; or ES_AUTOVSCROLL
        push    eax                     ; lpWindowName
        push    cls_edit                ; "EDIT"
        push    eax                     ; dwExStyle
        call    [CreateWindowExA]
        xchg    ebx, eax                ; ebx = hwnd

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
        call    [TranslateMessage]
        push    ebp
        call    [DispatchMessageA]
        jmp     msgloop

save:   push    0xFFF0
        push    edi
        push    ebx
        call    [GetWindowTextA]
        push    eax                     ; length
        xor     ecx, ecx
        push    ecx                     ; hTemplateFile
        push    0x80                    ; FILE_ATTRIBUTE_NORMAL
        push    2                       ; CREATE_ALWAYS
        push    ecx                     ; lpSecurityAttributes
        push    ecx                     ; no sharing
        push    0x40000000              ; GENERIC_WRITE
        push    savepath                ; "tinypad.txt" (COFF header bytes)
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
align 4
idata:
        dd      0, 0, 0                 ; OFT, TimeDateStamp, ForwarderChain
        dd      n_k32 - BASE
        dd      iat_k32 - BASE
        dd      0, 0, 0
        dd      n_u32 - BASE
        dd      iat_u32 - BASE
        dd      0, 0, 0, 0, 0           ; terminator
idata_end:

iat_k32:
CreateFileA      dd i_CreateFileA - BASE
WriteFile        dd i_WriteFile - BASE
CloseHandle      dd i_CloseHandle - BASE
ExitProcess      dd i_ExitProcess - BASE
        dd      0
iat_u32:
CreateWindowExA  dd i_CreateWindowExA - BASE
GetMessageA      dd i_GetMessageA - BASE
TranslateMessage dd i_TranslateMessage - BASE
DispatchMessageA dd i_DispatchMessageA - BASE
GetWindowTextA   dd i_GetWindowTextA - BASE
        dd      0

n_k32:  db      'kernel32.dll',0
n_u32:  db      'user32.dll',0

i_CreateFileA      dw 0
        db      'CreateFileA',0
i_WriteFile        dw 0
        db      'WriteFile',0
i_CloseHandle      dw 0
        db      'CloseHandle',0
i_ExitProcess      dw 0
        db      'ExitProcess',0
i_CreateWindowExA  dw 0
        db      'CreateWindowExA',0
i_GetMessageA      dw 0
        db      'GetMessageA',0
i_TranslateMessage dw 0
        db      'TranslateMessage',0
i_DispatchMessageA dw 0
        db      'DispatchMessageA',0
i_GetWindowTextA   dw 0
        db      'GetWindowTextA',0

filesize = $ - BASE
