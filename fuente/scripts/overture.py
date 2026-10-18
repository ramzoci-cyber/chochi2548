import pyarrow.fs as fs, pyarrow.dataset as ds, pyarrow.compute as pc, pyarrow.parquet as pq, os, sys, time
p = os.environ.get('HTTPS_PROXY')
s3 = fs.S3FileSystem(anonymous=True, region='us-west-2', proxy_options=p)
REL = 'overturemaps-us-west-2/release/2026-09-23.1'
XMIN, XMAX, YMIN, YMAX = -75.7170, -75.6690, -11.4480, -11.3755
OUT = sys.argv[1]
tipos = sys.argv[2:]
for tt in tipos:
    theme, typ = tt.split('/')
    t0 = time.time()
    d = ds.dataset(f'{REL}/theme={theme}/type={typ}/', filesystem=s3, format='parquet')
    f = ((pc.field('bbox', 'xmin') < XMAX) & (pc.field('bbox', 'xmax') > XMIN) &
         (pc.field('bbox', 'ymin') < YMAX) & (pc.field('bbox', 'ymax') > YMIN))
    tab = d.to_table(filter=f)
    pq.write_table(tab, f'{OUT}/{theme}_{typ}.parquet')
    print(tt, tab.num_rows, 'filas', round(time.time() - t0, 1), 's', flush=True)
