; Retrieved from: http://en.literateprograms.org/Hello_World_(Assembly_Intel_x86_Linux)?oldid=15308

section .data
msg	db	"Hello World!",0x0a

len	equ	$-msg

section .text
	global _start

_start:

	mov	ebx,0x01
	mov	ecx,msg
	mov	edx,len
	mov	eax,0x04
	int	0x80


	mov	ebx,0x00
	mov	eax,0x01
	int	0x80
