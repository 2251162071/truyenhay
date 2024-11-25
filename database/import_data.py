# Read the uploaded SQL file and filter out only the INSERT INTO statements
file_path = 'dump-truyenhay-202411230436.sql'
filtered_data_path = 'filtered-data.sql'

# Open the file and extract only the INSERT statements
with open(file_path, 'r', encoding='utf-8') as dump_file:
    lines = dump_file.readlines()

# Filter lines that contain 'INSERT INTO'
insert_statements = [line for line in lines if line.strip().startswith('INSERT INTO')]

# Write the filtered data to a new file
with open(filtered_data_path, 'w', encoding='utf-8') as filtered_file:
    filtered_file.writelines(insert_statements)
