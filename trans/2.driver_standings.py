# Databricks notebook source
dbutils.widgets.text("p_file_date", "2021-03-28")
v_file_date = dbutils.widgets.get("p_file_date")

# COMMAND ----------

# MAGIC %run "../includes/configuration"

# COMMAND ----------

# MAGIC %run "../includes/common_functions"

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC Find race year for which data to be reprocessed

# COMMAND ----------

race_results_df=spark.read.format("delta").load(f"{presentation_folder_path}/race_results") \
    .filter(f"file_date='{v_file_date}'") 

# COMMAND ----------

race_year_list=df_column_to_list(race_results_df,'race_year')

# COMMAND ----------

from pyspark.sql.functions import col;

race_results_df=spark.read.format("delta").load(f"{presentation_folder_path}/race_results") \
    .filter(col("race_year").isin(race_year_list))

# COMMAND ----------

from pyspark.sql.functions import col,sum,count, when
driver_standings_df=race_results_df \
.groupBy("race_year","driver_name","driver_nationality") \
.agg(sum("points").alias("total_points"), count(when(col("position")==1,True)).alias("wins"))

# COMMAND ----------

from pyspark.sql.window import Window
from pyspark.sql.functions import desc, rank

driver_rank_spec=Window.partitionBy("race_year").orderBy(desc("total_points"),desc("wins"))

final_df=driver_standings_df.withColumn("rank",rank().over(driver_rank_spec))

# COMMAND ----------

#final_df.write.mode("overwrite").format("parquet").saveAsTable("f1_presentation.driver_standings")

#overwrite_partition(final_df, 'f1_presentation', 'driver_standings', 'race_year')

# COMMAND ----------

merge_condition="tgt.driver_name=src.driver_name AND tgt.race_year=src.race_year"
merge_delta_data(final_df,'f1_presentation','driver_standings',presentation_folder_path, merge_condition, 'race_year')

# COMMAND ----------

# MAGIC %sql
# MAGIC 
# MAGIC SELECT * FROM
# MAGIC f1_presentation.driver_standings;

# COMMAND ----------

# MAGIC %sql
# MAGIC select race_id, count(1)
# MAGIC from f1_presentation.race_results
# MAGIC GROUP BY race_id
# MAGIC ORDER BY race_id desc

# COMMAND ----------

