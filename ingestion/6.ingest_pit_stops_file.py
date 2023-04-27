# Databricks notebook source
# MAGIC %md
# MAGIC #### ingest pit_stops.json file

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 1: Read the JSON file using the spark dataframe reader API

# COMMAND ----------

dbutils.widgets.text("p_data_source","")
v_data_source= dbutils.widgets.get("p_data_source")

# COMMAND ----------

dbutils.widgets.text("p_file_date","2021-03-21")
v_file_date=dbutils.widgets.get("p_file_date")

# COMMAND ----------

# MAGIC %run "../includes/configuration"

# COMMAND ----------

# MAGIC %run "../includes/common_functions"

# COMMAND ----------

from pyspark.sql.types import StructType, StructField, IntegerType, StringType

# COMMAND ----------

pit_stops_schema=StructType(fields=[StructField("raceId",IntegerType(), False),
                                   StructField("driverId",IntegerType(), True),
                                   StructField("stop",StringType(), True),
                                   StructField("lap",IntegerType(), True),
                                   StructField("time",StringType(), True),
                                   StructField("duration",StringType(), True),
                                   StructField("milliseconds",IntegerType(), True)
                                   ])

# COMMAND ----------

pit_stops_df=spark.read\
.schema(pit_stops_schema)\
.option("multiLine",True) \
.json(f"{raw_folder_path}/{v_file_date}/pit_stops.json")

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 2: Rename columns and add new columns
# MAGIC 
# MAGIC 1. Rename driverId and RaceId
# MAGIC 1. Add Ingestion_Date with current timestamp

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, lit

# COMMAND ----------

final_df=pit_stops_df.withColumnRenamed("driverId","driver_id") \
.withColumnRenamed("raceId","race_id") \
.withColumn("data_source",lit(v_data_source)) \
.withColumn("file_date",lit(v_file_date))   

# COMMAND ----------

final_df=add_ingestion_date(final_df)

# COMMAND ----------

# MAGIC %md
# MAGIC ##### Step 3: Write putput to processed container in parquet format

# COMMAND ----------

# MAGIC %sql 
# MAGIC --DROP TABLE f1_processed.pit_stops;

# COMMAND ----------

#overwrite_partition(final_df, 'f1_processed', 'pit_stops', 'race_id')

# COMMAND ----------

merge_condition="tgt.race_id=src.race_id AND tgt.driver_id=src.driver_id AND tgt.stop=src.stop AND tgt.race_id=src.race_id"
merge_delta_data(final_df,'f1_processed','pit_stops',processed_folder_path, merge_condition, 'race_id')

# COMMAND ----------

#final_df.write.mode("overwrite").format("parquet").saveAsTable("f1_processed.pit_stops")

# COMMAND ----------

dbutils.notebook.exit("Success")

# COMMAND ----------

# MAGIC %sql
# MAGIC 
# MAGIC SELECT race_id, count(1)
# MAGIC FROM f1_processed.pit_stops
# MAGIC GROUP BY race_id
# MAGIC ORDER BY race_id DESC

# COMMAND ----------

