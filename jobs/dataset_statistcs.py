from pyspark.sql import SparkSession
import pyspark.sql.functions as F

MASTER_URL = "spark://spark:7077"
DATA_PATH = "/data/traffic.parquet/"

spark = SparkSession.builder.master(MASTER_URL).getOrCreate()
# Reduce logging
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.parquet(DATA_PATH)

# Prit unique CLASSIFICAÇÃO values
(
    df
    .groupBy( F.col("CLASSIFICAÇÃO") )
    .count()
    .show()
)

# Count total number of rows
print(
    df
    .count()
)