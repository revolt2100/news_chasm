import json
import re

def process_text_content():
    input_file = 'filtered_holod.json'
    output_file = 'filtered_text_holod.json'
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle structure (list or dict with articles)
    if isinstance(data, list):
        articles = data
        is_list = True
    elif isinstance(data, dict) and 'articles' in data:
        articles = data['articles']
        is_list = False
    else:
        articles = [data] if isinstance(data, dict) else []
        is_list = isinstance(data, list)
    
    for article in articles:
        if not isinstance(article, dict) or 'Text' not in article:
            continue
        
        text = article['Text']
        
        # 2. Remove from "Общество\n\n" through the share buttons section
        # Pattern matches: Общество\n\n[anything]\n\nОтправить\n\nПоделиться...\n\n
        removal_pattern = r'Общество\n\n.*?\n\nОтправить\n\nПоделиться\n\nПоделиться\n\nПоделиться\n\nПоделиться\n\n'
        text = re.sub(removal_pattern, '', text, count=1, flags=re.DOTALL)
        
        # 3. Remove donation footer: everything after subscription prompt
        # Handle non-breaking spaces (\xa0) between "не" and "пропускать"
        footer_pattern = r'\n\nЧтобы не\s+пропускать главные материалы «Холода».*'
        text = re.sub(footer_pattern, '', text, flags=re.DOTALL)
        
        removal_pattern2 = r'\n\nМы ставим в центр своей журналистики человека и рассказываем о людях.*'
        text = re.sub(removal_pattern2, '', text, count=1, flags=re.DOTALL)
        # Clean up extra whitespace/newlines
        article['Text'] = text.strip()
    
    # Save output maintaining original structure
    if is_list:
        output_data = articles
    else:
        output_data = {**data, 'articles': articles}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"Processing complete. File saved as: {output_file}")

if __name__ == "__main__":
    process_text_content()