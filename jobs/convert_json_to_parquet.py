from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, LongType, TimestampType

import os

MASTER_URL = 'spark://spark:7077'

spark = SparkSession.builder\
.master(MASTER_URL)\
.appName('transformParquet')\
.getOrCreate()


# Get all JSON files from the path
# /data/AGOSTO_2022/20220801/20220801_00.json
BASE_PATH = '/data/'
WRITE_PATH = '/data/traffic.parquet'

SCHEMA = StructType([
    StructField("ID EQP", LongType()),
    StructField("DATA HORA", TimestampType()),
    StructField("MILESEGUNDO", LongType()),
    StructField("CLASSIFICAÇÃO", StringType()),
    StructField("FAIXA", LongType()),
    StructField("ID DE ENDEREÇO", LongType()),
    StructField("VELOCIDADE DA VIA", StringType()),
    StructField("VELOCIDADE AFERIDA", StringType()),
    StructField("TAMANHO", StringType()),
    StructField("NUMERO DE SÉRIE", LongType()),
    StructField("LATITUDE", StringType()),
    StructField("LONGITUDE", StringType()),
    StructField("ENDEREÇO", StringType()),
    StructField("SENTIDO", StringType())
])

# Get all the folders from the base path
folders = [
    os.path.join(BASE_PATH, f) 
    for f in os.listdir(BASE_PATH) 
    if os.path.isdir(os.path.join(BASE_PATH, f))
]

# Get all json files from the folders
json_files = {
    folder: [
        os.path.join(folder, f) 
        for f in os.listdir(folder)
        if f.endswith('.json')
    ]
    for folder in folders
}

print(json_files)
print(len(json_files))

# Transform all files into parquet

df = None
for folder, files in json_files.items():
    print(
        f"""\n
        Transforming files from {folder}
        Total files: {len(files)}
        """
    )
    
    if df == None:
        df = spark\
        .read\
        .option("multiline", "true")\
        .json(files, schema=SCHEMA)
        df.show()

    df = df.union(
        spark\
        .read\
        .option("multiline", "true")\
        .json(files, schema=SCHEMA)
    )
    
df.show()

df = (
    df
    .select(
        [
            'DATA HORA',
            'CLASSIFICAÇÃO',
            'LATITUDE',
            'LONGITUDE'
        ]
    )
    .withColumn( 'YEAR', F.year('DATA HORA') )
    .withColumn( 'MONTH', F.month('DATA HORA') )
    .withColumn( 'DAY', F.dayofmonth('DATA HORA') )
)

df\
.write\
.mode('overwrite')\
.partitionBy('YEAR', 'MONTH', 'DAY')\
.parquet(WRITE_PATH)

spark.stop()