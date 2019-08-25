# Disk usage visualizer

This is a simple script to help visualize the usage of your ext2/3/4 partitions on a linux system.

![Boot partition](samples/boot.png)
![Root partition](samples/root.png)

## Building/running

1. Install requirements

*Dependencies will vary for other systems. This is ubuntu*

    sudo apt install e2fsprogs python3-pil
    # Find the filesystem you want to inspect, check that it is ext
    mount

2. Run the script

*Note that the images generated can be very large if your partition is large*

    ./usage.py /dev/sda1 # Shows image on screen
    ./usage.py /dev/sda1 boot.png # Writes image to file
    ./usage.py - < dump.txt # Generate image from saved dump file


## How its done

dumpe2fs dumps stats about an ext2/3/4 partition, chiefly which blocks are used, free, descriptors, etc. So I run dumpe2fs and parse the results, then use PIL to generate an image to see what's happening there.

    sudo dumpe2fs /dev/sda1
    sudo dumpe2fs /dev/mapper/ubuntu--vg-root

Total blocks on partition
> Block count:              187136

Each group occupies a range of blocks
> Group 0: (Blocks 0-32767) csum 0xfbb1 [ITABLE_ZEROED]

Special block descriptions
>   Primary superblock at 0, Group descriptors at 1-1 # Absolute values
>   Reserved GDT blocks at 2-92 # Absolute values
>   Block bitmap at 93 (+93), csum 0x300994ca
>   Inode bitmap at 99 (+99), csum 0x807db3a8
>   Inode table at 105-592 (+105)

Free blocks(a-b, c-d, e-f, are absolute values)
>   Free blocks: 3045-32767
