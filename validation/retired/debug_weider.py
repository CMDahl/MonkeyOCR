import pandas as pd

df = pd.read_csv('comprehensive_comparison_dataframe.csv')
flagged = pd.read_csv('flagged_job_overlap_records.csv')

# Get WEIDER, Aasta record
weider = flagged[flagged['name_azure'] == 'WEIDER, Aasta'].iloc[0]
print('Flagged record:')
print(f'Book ID: {weider["book_id"]}')
print(f'Name Azure: {weider["name_azure"]}')
print(f'Name Monkey: {weider["name_monkey"]}')
print()

print('Searching in comparison data...')
matches = df[
    (df['book_id'] == weider['book_id']) & 
    (df['name_azure'] == weider['name_azure']) & 
    (df['name_monkey'] == weider['name_monkey'])
]
print(f'Found {len(matches)} matches')

if len(matches) > 0:
    print(f'All matching records:')
    for idx, record in matches.iterrows():
        print(f'\nRecord {idx}:')
        print(f'  Azure markdown: {str(record["markdown_chunk_azure"])[:100]}...')
        print(f'  Monkey markdown: {str(record["markdown_chunk_monkey"])[:100]}...')
        print(f'  Job titles:')
        for i in range(1, 6):
            azure_job = record.get(f'job{i}_title_azure', 'Missing')
            monkey_job = record.get(f'job{i}_title_monkey', 'Missing')
            print(f'    Job {i}: Azure="{azure_job}", Monkey="{monkey_job}"')
    
    print(f'\nUsing first record (index {matches.index[0]}):')
    record = matches.iloc[0]
    print(f'Azure markdown: {str(record["markdown_chunk_azure"])[:300]}...')
    print()
    print(f'Monkey markdown: {str(record["markdown_chunk_monkey"])[:300]}...')
    print()
    print('Job titles:')
    for i in range(1, 6):
        azure_job = record.get(f'job{i}_title_azure', 'Missing')
        monkey_job = record.get(f'job{i}_title_monkey', 'Missing')
        print(f'Job {i}: Azure="{azure_job}", Monkey="{monkey_job}"')
else:
    print('No matches found!')
    print('Available book_ids in comparison data:')
    book_ids = df['book_id'].unique()
    matching_book_ids = [bid for bid in book_ids if weider['book_id'] in bid]
    print(matching_book_ids[:10])
