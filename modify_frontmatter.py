'''
Script to Bulk Modify Frontmatter in Markdown Files
'''

import os
import glob
from datetime import datetime
from io import BytesIO

import frontmatter


def generate_file_slug(source_directory: str, filepath: str) -> str:
    '''
    Function to generate the Slug Attribute
    '''

    filepath = (
        filepath
        .removeprefix(source_directory)
        .removesuffix('.md')
        .lower()
        .replace("'", '')
    )

    # For Main Index File set slug as '/' (Root)
    if filepath.count('/') == 1 and filepath.find('index') != 1:
        return '/'

    slug = (
        filepath
        .replace('&', 'and')
        .replace('(', '')
        .replace(')', '')
        .replace(' - ', '-')
        .replace('.', '')
        .replace('  ', ' ')
        .replace(' ', '-')
    )

    # Check if the File is an Intermediate Index if so remove filename
    starting_part, folder_name, ending_part = slug.rsplit('/', maxsplit=2)
    if (
        folder_name == ending_part or
        (ending_part.find('index') != -1 and ending_part == f'{folder_name} index')
    ):
        return f'{starting_part}/{folder_name}'

    return slug


def generate_file_title(filepath: str) -> str:
    '''
    Function to generate the Title Attribute
    '''

    # Gets the Filename from filepath
    file_title = filepath.removesuffix('.md').rsplit('/', maxsplit=1)[1]

    return file_title


def generate_file_id(filepath: str) -> str:
    '''
    Function to generate the Id Attribute
    '''

    # Generate the File Id from the filename
    filename = filepath.removesuffix('.md').rsplit('/', maxsplit=1)[1]
    file_id = (
        filename
        .replace('&', 'and')
        .replace(',', '')
        .replace('(', '')
        .replace(')', '')
        .replace(' - ', '-')
        .replace('  ', ' ')
        .replace(' ', '-')
        .lower()
    )

    return file_id


def generate_file_update_date(filepath: str) -> str:
    '''
    Function to generate the Last Updated Attribute

    Note:
    The actual modified timestamp is incremented by a small value to account
    for the time taken for program to write the modifications to file
    '''

    # Return the Last Modified Time of File (with a small increment)
    modified_time = os.stat(filepath).st_mtime
    return datetime.fromtimestamp(modified_time + 120).strftime('%Y-%m-%d %H:%M:%S')


def check_if_file_was_modified(
    filepath: str, current_file: frontmatter.Post, force_edit_files: bool
) -> bool:
    '''
    Function to check if the file was modified since last commit
    force_edit_files: If True will modify file even if modified date is not changed
    '''

    if force_edit_files:
        return True

    if frontmatter.check(filepath) and current_file.metadata.get('last_updated'):
        frontmatter_modified_time = (
            datetime
            .strptime(current_file.metadata['last_updated'], '%Y-%m-%d %H:%M:%S')
        )
        system_modified_time = (
            datetime
            .fromtimestamp(os.stat(filepath).st_mtime)
            .replace(microsecond=0)
        )

        return system_modified_time > frontmatter_modified_time

    return True


def generate_required_frontmatter(
    current_file: frontmatter.Post, source_directory: str, filepath: str
) -> None:
    '''
    Function to Generate the Required Frontmatter Fields
    '''

    current_file.metadata['id'] = generate_file_id(filepath)
    current_file.metadata['slug'] = generate_file_slug(source_directory, filepath)
    current_file.metadata['title'] = generate_file_title(filepath)
    current_file.metadata['last_updated'] = generate_file_update_date(filepath)

    # View File Frontmatter
    print(current_file.metadata, '\n')


def save_modified_frontmatter_to_file(
    current_file: frontmatter.Post, normalized_filepath: str
) -> None:
    '''
    Write the modified frontmatter to File
    '''

    output_file = BytesIO()
    frontmatter.dump(current_file, output_file)

    # View Content that will be written to file
    # print(output_file.getvalue().decode('utf-8'))

    with open(normalized_filepath, mode='wb') as result_file:
        output_file.seek(0)
        result_file.write(output_file.read())


def main(*args, **kwargs) -> int:
    '''
    Main Driver Function
    '''

    # Script Options
    source_directory = './docs'
    source_file_path = f'{source_directory}/**/*.md'
    force_edit_files = True

    for filepath in glob.iglob(source_file_path, recursive=True):

        normalized_filepath = filepath.replace('\\', '/')
        print(normalized_filepath)

        with open(normalized_filepath, encoding='utf-8') as markdown_file:
            current_file = frontmatter.load(markdown_file)

        if check_if_file_was_modified(normalized_filepath, current_file, force_edit_files):

            generate_required_frontmatter(current_file, source_directory, normalized_filepath)
            save_modified_frontmatter_to_file(current_file, normalized_filepath)

        else:
            print('File is upto date\n')

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
