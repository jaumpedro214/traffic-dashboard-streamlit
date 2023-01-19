from pyspark.sql import SparkSession
import pyspark.sql.functions as F

MASTER_URL = "spark://spark:7077"
DATA_PATH = "/data/traffic.parquet/"

TIME_WINDOW = "15 minutes"

spark = SparkSession.builder.master(MASTER_URL).getOrCreate()
# Reduce logging
spark.sparkContext.setLogLevel("ERROR")

df = spark.read.parquet(DATA_PATH)

# Normalizing the CLASSIFICAÇÃO column
df = (
    df
    .withColumn(
        "CLASS",
        F.when(
            F.col("CLASSIFICAÇÃO") == "CAMINHÃO", "CAMINHAO_ONIBUS"
        )
        .when(
            F.col("CLASSIFICAÇÃO") == "ÔNIBUS", "CAMINHAO_ONIBUS"
        )
        .when(
            F.col("CLASSIFICAÇÃO") == "CAMINHÃO / ÔNIBUS ", "CAMINHAO_ONIBUS"
        )
        .when(
            F.col("CLASSIFICAÇÃO") == "AUTOMÓVEL", "AUTOMOVEL"
        )
        .otherwise(F.col("CLASSIFICAÇÃO"))
    )
    .drop("CLASSIFICAÇÃO")
)

# Count the number of vehicles of each time in a window 
df = (
    df
    .groupBy(
        F.window(
            F.col("DATA HORA"),
            TIME_WINDOW
        )
        .alias("TIME_WINDOW"),
        F.col("CLASS"),
        F.col("LATITUDE"),
        F.col("LONGITUDE"),
    )
    .agg(
        F.count("*").alias("COUNT"),
        F.min("DATA HORA").alias("MIN_TIME"),
    )
    .withColumn(
        "MONTH", F.month(F.col("MIN_TIME")),
    )
)

# Save as parquet
(
    df
    .write
    .mode("overwrite")
    .partitionBy("MONTH", "CLASS")
    .parquet("/data/vehicles_count.parquet")
)