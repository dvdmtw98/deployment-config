'''
Script to modify Image Links, Outgoing Links & Callouts in Markdown Files

Markdown Link Regex:
https://davidwells.io/snippets/regex-match-markdown-links
https://stephencharlesweiss.com/regex-markdown-link

Kramdown Syntax:
https://kramdown.gettalong.org/syntax.html

Callout Block Regex:
https://github.com/sondregronas/mkdocs-callouts/blob/main/src/mkdocs_callouts/utils.py
https://github.com/Pseudonium/Obsidian_to_Anki/issues/332
'''

from __future__ import annotations
import re
import os
import glob


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


def perform_file_transformation(
    source_filepath: str, site_generator: str,
    link_regex_pattern: str, callout_regex_pattern: str
) -> None:
    '''
    Main function to call the transformation logic
    '''

    with open(source_filepath, "r", encoding='utf-8') as input_file:
        file_content = input_file.read()

    # Process Index file
    markdown_filename = os.path.basename(os.path.splitext(source_filepath)[0])
    if markdown_filename in ["Main Index"]:
        file_content = process_main_index(file_content, link_regex_pattern)

    # Process Links
    links_from_file = re.finditer(link_regex_pattern, file_content, flags=re.I)
    for link in links_from_file:
        if link.group(0).startswith("!["):
            file_content = process_images(file_content, link, site_generator)
        else:
            file_content = process_outgoing_links(file_content, link, site_generator)

    # Process Callouts
    callout_mapping = {
        'tip': ['tip', 'hint', 'important'],
        'info': ['info', 'note'],
        'warning': ['warning', 'caution', 'attention'],
        'danger': ['danger', 'error']
    }

    callouts_from_file = re.finditer(callout_regex_pattern, file_content, flags=re.I | re.M)
    for callout in callouts_from_file:
        file_content = process_callouts(file_content, callout, callout_mapping, site_generator)

    with open(source_filepath, "w", encoding='utf-8') as output_file:
        output_file.write(file_content)


def process_main_index(file_content: str, link_regex_pattern: str) -> str:
    '''
    Function to remove entries from Index file
    '''

    accumulated_file = ''
    for line in file_content.splitlines():
        search_result = re.search(link_regex_pattern, line.rstrip('\n'))
        if search_result:
            if search_result.group(2) not in ["Read & Watch List", "Languages"]:
                accumulated_file += f'{line}\n'
        else:
            accumulated_file += f'{line}\n'

    return accumulated_file


def process_callouts(
    file_content: str, callout_match: re.Match,
    callout_mapping: dict[str, list[str]], site_generator: str
) -> str:
    '''
    Function to modify callouts
    '''

    if callout_match.group(5) or site_generator == "mkdocs":
        return file_content

    callout_type = callout_match.group(2).lower()
    callout_title = callout_match.group(3).strip() if callout_match.group(3).strip() else ''
    callout_body = callout_match.group(4)

    kramdown_type = None
    for chirpy_type, obsidian_types in callout_mapping.items():
        if callout_type in obsidian_types:
            kramdown_type = chirpy_type
    kramdown_type = kramdown_type if kramdown_type else 'info'
    kramdown_attributes = f'{{: .prompt-{kramdown_type} }}'

    if callout_title:
        modified_callout = f'> **{callout_title}**  \n{callout_body}\n{kramdown_attributes}'
    else:
        modified_callout = f'{callout_body}\n{kramdown_attributes}'

    original_callout = callout_match.group(1)
    file_content = file_content.replace(original_callout, modified_callout)
    return file_content


def process_outgoing_links(file_content: str, link_match: re.Match, site_generator: str) -> str:
    '''
    Function to modify the outgoing hyperlinks
    '''

    original_link = link_match.group(1)

    if link_match.group(5) or not link_match.group(3).startswith(("http", "https")):
        return file_content

    if site_generator == 'mkdocs':
        kramdown_attributes = '{: target="_blank" rel="noopener noreferrer" style="text-decoration:underline" }'
    else:
        kramdown_attributes = '{: target="_blank" rel="noopener noreferrer" }'

    description = link_match.group(2).replace("|", r"\|")
    outgoing_link = link_match.group(3)

    modified_link = f'[{description}]({outgoing_link}){kramdown_attributes}'

    file_content = file_content.replace(original_link, modified_link)
    return file_content


def process_images(file_content: str, image_match: re.Match, site_generator: str) -> str:
    '''
    Function to Convert Markdown Image links to Kramdown Image Links
    '''

    if image_match.group(5):
        return file_content

    description = image_match.group(2).rsplit('|')
    image_link = image_match.group(3)

    if len(description) > 1:
        if site_generator == "mkdocs":
            modified_image = f'![{description[0]}]({image_link}){{: style="width:{description[1]}px" }}'
        else:
            modified_image = f'![{description[0]}]({image_link}){{: width="{description[1]}" .shadow }}'
    else:
        if site_generator == "mkdocs":
            modified_image = f'![{description[0]}]({image_link}){{: style="width:640px" }}'
        else:
            modified_image = f'![{description[0]}]({image_link}){{: width="640" .shadow }}'

    original_image = image_match.group(1)
    file_content = file_content.replace(original_image, modified_image)
    return file_content


def on_pre_build(**kwargs) -> None:
    '''
    Main driver function
    '''

    print('Starting: "modify_links" script...')

    links_regex_pattern = r'(!?\[([^\]]*)?\]\(((?:https?://)?[A-Za-z0-9:/.%&#-_ ]+)(?:"(.+)")?\))({:(?:.+)})?'
    callout_regex_pattern = r'((?:>+) *\[!([^\]]*)\](.*)?\n(.+(?:\n(?:^.{1,3}$|^.{4}(?<!<!--).*))*))({:(?:.+)})?'

    source_directory, site_generator = source_directory_selector(**kwargs)
    source_file_path = os.path.join(f'{source_directory}', '**', '*.md')

    for filepath in glob.iglob(source_file_path, recursive=True):
        print(filepath)
        perform_file_transformation(filepath, site_generator, links_regex_pattern, callout_regex_pattern)

    print('Completed: "modify_links" script...')


if __name__ == '__main__':
    on_pre_build()
