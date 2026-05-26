import json
import os
from urllib.parse import urlparse, unquote

# Имена файлов и папок
INPUT_JSON_PATH = 'filtered_holod.json'  # Ваш исходный файл
OUTPUT_JSON_PATH = 'labeled.json' # Файл, который получится на выходе
ILLUSTRATIONS_DIR = 'labeled_all_illustrations'
PHOTOS_DIR = 'labeled_all_photos'

def main():
    # 1. Считываем имена файлов из папки с иллюстрациями
    try:
        # Получаем список всех файлов в папке иллюстраций
        illustrations_files = set(os.listdir(ILLUSTRATIONS_DIR))
    except FileNotFoundError:
        print(f"Ошибка: Папка '{ILLUSTRATIONS_DIR}' не найдена в текущей директории.")
        return

    # 2. Открываем исходный JSON файл
    try:
        with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
            articles = json.load(f)
    except FileNotFoundError:
        print(f"Ошибка: Файл '{INPUT_JSON_PATH}' не найден.")
        return

    # 3. Проходим по всем статьям и заменяем формат картинок
    for article in articles:
        labeled_images = []
        
        # Получаем текущий список ссылок (если картинок нет, будет пустой список)
        images = article.get("Images", [])
        
        for img_url in images:
            # Парсим ссылку и достаем название файла
            parsed_url = urlparse(img_url)
            # unquote нужен, чтобы %20 превратился в пробел и т.д.
            filename = unquote(os.path.basename(parsed_url.path))
            
            # Если имя файла есть в папке иллюстраций, ставим 1, иначе 0
            if filename in illustrations_files:
                is_illustration = 1
            else:
                is_illustration = 0
                
            # Добавляем в новый список в виде словаря
            labeled_images.append({
                "url": img_url,
                "Is illustration": is_illustration
            })
            
        # Обновляем ключ Images в статье
        article["Images"] = labeled_images

    # 4. Сохраняем результат в новый JSON файл
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(articles, f, ensure_ascii=False, indent=2)
        
    print(f"Успешно обработано {len(articles)} статей!")
    print(f"Результат сохранен в файл: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    main()