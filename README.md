# VectorTextFieldStatistics

*The aim of this plugin is to help visualise the contents of text fields in Vector layers.*

I wrote this originally to help me visualise the wide, sparse text tables which are typical of OpenStreetMap data brought in via osm2pgsql. Such tables have dozens of fields, most of which are null for most records.

When planning mapping, it can be useful to know the discrete values for each field, and how often each value happens. This can also help with assessing the quality and consistency of the data.

When you choose from the list of Vector layers, the features in that layer and scanned and a list of text fields is shown below.

The colour of the field name gives a clue to its type. This can be useful when examining an unfamiliar data source

+ red - unique id field. No NULLs, no repeated values. Likely to be a primary key
+ orange - no repeated values, but some NULL values
+ black - repeated values, some NULL values
+ grey - every value is NULL, field is empty for all records
+ blue - repeated values, no NULL values

When you expand the fieldname, a list of discrete values for that field is given. By default this is sorted alphabetically, or you can choose to sort by frequency (most common values appear first). You can also choose whether or not to show NULL values, or whether or not to hide fields which only have NULL values.
