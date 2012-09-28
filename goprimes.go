package main

import (
	"flag"
	"fmt"
)

func counter(start uint64) chan uint64 {
	var output = make(chan uint64)
	go func() {
		for i := start; ; i++ {
			output <- i
		}
	}()
	return output
}

func filter(prime uint64, input chan uint64) chan uint64 {
	var output = make(chan uint64)
	go func() {
		for {
			if i := <-input; i%prime != 0 {
				output <- i
			}
		}
	}()
	return output
}

func main() {
	var n = flag.Int("n", 5, "amount of prime numbers to generate")
	flag.Parse()
	var c = counter(2)
	for i := 0; i < *n; i++ {
		var prime = <-c
		c = filter(prime, c)
		fmt.Println(prime)
	}
}
