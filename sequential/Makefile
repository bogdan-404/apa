CC = gcc
CFLAGS = -O2 -Wall -Wextra -std=c11
TARGET = prime_sequential

.PHONY: all clean run

all: $(TARGET)

$(TARGET): prime_sequential.c
	$(CC) $(CFLAGS) -o $(TARGET) prime_sequential.c

run: $(TARGET)
	./$(TARGET) 100000

clean:
	rm -f $(TARGET)
