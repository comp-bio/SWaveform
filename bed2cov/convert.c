#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char *argv[])
{
    char buf[BUFSIZ];
    char delim[] = "\t";
    char chr_last[256];
    unsigned int position = 0;
    FILE * f = NULL;

    while (fgets(buf, sizeof buf, stdin)) {
        char * ptr = strtok(buf, delim);
        char chr[256];
        strcpy(chr, ptr);
        
        unsigned int start;
        unsigned int stop;
        unsigned int coverage;

        if (strcmp(chr_last, chr) != 0) {
            if (f != NULL) {
                fclose(f);
                position = 0;
            }
            strcpy(chr_last, chr);
            strcat(chr, ".bcov");
            f = fopen(chr, "wb");
        }

        ptr = strtok(NULL, delim);
        start = atoi(ptr);

        ptr = strtok(NULL, delim);
        stop = atoi(ptr);

        ptr = strtok(NULL, delim);

        if (ptr != NULL) {
            coverage = atoi(ptr);
        } else {
            coverage = stop;
            stop = start + 1;
        }

        while (position < start) {
            fputc(0, f);
            fputc(0, f);
            position++;
        }

        if (coverage > 255 * 255) coverage = 255 * 255;

        while (position < stop) {
            fputc((coverage >> 8) & 0xFF, f);
            fputc(coverage & 0xFF, f);
            position++;
        }
    }

    fclose(f);
    return 0;
}

// Build: gcc bed2cov/convert.c -std=c99 -m64 -O3 -o bed2cov/convert_$(uname)
// Usage: cat file.bed | ./convert_Linux
