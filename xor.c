#include <unistd.h>
#include <string.h>

int main(int argc, char *argv[]){
  char buff[1024];
  int n, a, b=0, kl=0;

  if(argc<2) return 0;
  kl = strlen(argv[1]);

  while((n = read(STDIN_FILENO, buff, sizeof buff))>0){
    for(a=0; a<n; a++, b++)
      buff[a] ^= argv[1][b%kl];

    write(STDOUT_FILENO, buff, n);
  }

  return 0;
}
