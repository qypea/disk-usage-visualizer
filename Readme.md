Analysing and visualizing disk usage
====================================


    sudo dumpe2fs /dev/sda1
    sudo dumpe2fs /dev/mapper/ubuntu--vg-root

Total blocks on partition
> Block count:              187136

Each group occupies a range of blocks
> Group 0: (Blocks 0-32767) csum 0xfbb1 [ITABLE_ZEROED]

Special block descriptions(at X is offset from start)
>   Primary superblock at 0, Group descriptors at 1-1
>   Reserved GDT blocks at 2-92
>   Block bitmap at 93 (+93), csum 0x300994ca
>   Inode bitmap at 99 (+99), csum 0x807db3a8
>   Inode table at 105-592 (+105)

Free blocks(a-b, c-d, e-f, are absolute values)
>   Free blocks: 3045-32767
