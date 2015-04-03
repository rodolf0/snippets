// http://stackoverflow.com/a/7848776
package main

import (
	"log"
	"net"
)

func main() {
	maddr, err := net.ResolveUDPAddr("udp", "239.0.0.1:1234")
	if err != nil {
		log.Fatalln("Failed to resolve UDP addr")
	}

	mconn, err := net.ListenMulticastUDP("udp", nil, maddr)
	if err != nil {
		log.Fatalln("Failed to listen at UDP addr")
	}

	wconn, err := net.DialUDP("udp", nil, maddr)
	if err != nil {
		log.Fatalln("Failed to blah")
	}

	buf := make([]byte, 96)
	for i := 0; i < 10; i++ {
		n, err := mconn.Read(buf)

		if err != nil {
			log.Fatalln("Failed to read from UDP conn")
		}

		log.Printf("Read %v bytes: %v\n", n, string(buf[:n]))

		n, err = wconn.Write(append([]byte("pong"), buf[:n]...))

		if err != nil {
			log.Fatalln("Failed to write to UDP conn", err)
		}
	}
}
