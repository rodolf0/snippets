TARGET=hello_world

all: $(TARGET)

$(TARGET):
	nasm -f elf64 hello_world.asm
	ld -o hello_world hello_world.o

clean:
	rm -f *.o $(TARGET)
