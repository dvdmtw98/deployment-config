'''
Script to modify Markdown Links in Markdown Files

References:
https://davidwells.io/snippets/regex-match-markdown-links
https://stephencharlesweiss.com/regex-markdown-link
https://kramdown.gettalong.org/syntax.html
'''

from __future__ import annotations
from typing import TextIO
import re
import os
import glob


def perform_file_transformation(
    regex_pattern: str, source_filepath: str,
    common_image_extensions: tuple[str], common_outgoing_extensions: tuple[str],
    site_generator: str
) -> None:
    '''
    Function to call the required transformation function
    '''

    destination_filepath = source_filepath.rstrip('.md') + ' Temp.md'

    # This function is only executed on the Main Index file
    if source_filepath.find("Main Index") != -1:
        with open(source_filepath, "r", encoding='utf-8') as input_file, \
                open(destination_filepath, "w", encoding='utf-8') as output_file:

            process_main_index_content(input_file, output_file, regex_pattern)

        os.replace(destination_filepath, source_filepath)

    if source_filepath.find("Various Lists") == -1:
        # This function is used to process the image links that are present in the file
        with open(source_filepath, "r", encoding='utf-8') as input_file, \
                open(destination_filepath, "w", encoding='utf-8') as output_file:

            process_file_image_links(
                input_file, output_file,
                regex_pattern, common_image_extensions
            )

        os.replace(destination_filepath, source_filepath)

        # This function is used to process the hyperlinks that are present in the file
        with open(source_filepath, "r", encoding='utf-8') as input_file, \
                open(destination_filepath, "w", encoding='utf-8') as output_file:

            process_file_outgoing_links(
                input_file, output_file,
                regex_pattern, common_outgoing_extensions,
                site_generator
            )

        os.replace(destination_filepath, source_filepath)


def process_file_outgoing_links(
    input_file: TextIO, output_file: TextIO,
    regex_pattern: str, common_link_extensions: tuple[str],
    site_generator: str
) -> None:
    '''
    Function to modify the hyperlinks that are present in the files
    '''

    for line in input_file:
        search_result = re.search(regex_pattern, line.rstrip('\n'))

        if (
            search_result and not search_result.group(0).startswith('!') and
            search_result.group(2).startswith(common_link_extensions)
        ):
            # print(search_result.group(0))
            match_end_index = search_result.end()

            if site_generator == 'mkdocs':
                kramdown_attributes = '{: target="_blank" rel="noopener noreferrer" style="text-decoration:underline" }'
            else:
                kramdown_attributes = '{: target="_blank" rel="noopener noreferrer" }'

            if line.find('{:', match_end_index, match_end_index + 2) == -1:
                new_link_format = search_result.group(0) + kramdown_attributes
                modified_line = re.sub(regex_pattern, new_link_format, line)
                output_file.write(modified_line)
            else:
                output_file.write(line)

        else:
            output_file.write(line)


def process_main_index_content(
    input_file: TextIO, output_file: TextIO, regex_pattern: str
) -> None:
    '''
    Function to remove Various Lists from Index
    '''

    for line in input_file:
        search_result = re.search(regex_pattern, line.rstrip('\n'))

        if search_result:
            if search_result.group(1) not in ["Read & Watch List", "Languages"]:
                output_file.write(line)
        else:
            output_file.write(line)


def process_file_image_links(
    input_file: TextIO, output_file: TextIO,
    regex_pattern: str, common_image_extensions: tuple[str]
) -> None:
    '''
    Function to Convert Markdown Image links to Mkdocs Image Links
    '''

    for line in input_file:
        search_result = re.search(regex_pattern, line.rstrip('\n'))

        if (
            search_result and search_result.group(0).startswith('!') and
            search_result.group(2).endswith(common_image_extensions)
        ):
            # print(search_result.group(0))
            description_part = search_result.group(1).rsplit('|')

            if len(description_part) > 1:
                output_file.write(
                    f'![{description_part[0]}]({search_result.group(2)})'
                    f'{{: style="width:{description_part[1]}px" }}\n'
                )
            else:
                output_file.write(line)
        else:
            output_file.write(line)


def source_directory_selector(**kwargs: dict[str, dict | list]) -> tuple[str, str]:
    '''
    Function to check which Static Generator is being used
    '''

    # print(kwargs)
    if kwargs and kwargs.get('config').get('docs_dir'):
        source_directory = kwargs.get('config').get('docs_dir')
        site_generator = 'mkdocs'
    else:
        source_directory = '_posts'
        site_generator = 'jekyll'

    return source_directory, site_generator


def on_pre_build(**kwargs) -> None:
    '''
    Main driver function code
    '''

    print('Starting: "modify_links" script...')

    # Regex to select Markdown Links
    regex_pattern = r'!?\[([^\]]*)?\]\(((https?:\/\/)?[A-Za-z0-9\:\/\. %&-_]+)(\"(.+)\")?\)'
    common_image_extensions = ('.png', '.gif', '.jpg', '.jpeg', '.webp')
    common_link_extensions = ('http://', 'https://')

    source_directory, site_generator = source_directory_selector(**kwargs)
    # print(source_directory)
    source_file_path = f'{source_directory}/**/*.md'
    # print(source_file_path)

    for filepath in glob.iglob(source_file_path, recursive=True):

        normalized_filepath = filepath.replace('\\', '/')
        print(normalized_filepath)

        perform_file_transformation(
            regex_pattern, normalized_filepath,
            common_image_extensions, common_link_extensions,
            site_generator
        )

    print('Completed: "modify_links" script...')


if __name__ == '__main__':
    on_pre_build()
