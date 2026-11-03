%%time
!find /kaggle/usr/lib -type f -print0 | xargs -0 -P 32 -n 500 cat > /dev/null