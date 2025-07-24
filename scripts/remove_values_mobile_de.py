#!/usr/bin/env python3
"""
Remove o campo 'value' das marcas e modelos do arquivo mobile_de_database.json
"""

import json
from pathlib import Path

def remove_values_from_mobile_de(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for brand in data['brands'].values():
        # Remove 'value' da marca, se existir
        brand.pop('value', None)
        for model in brand['models']:
            model.pop('value', None)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Arquivo salvo sem os campos 'value': {output_path}")


def main():
    input_path = 'data/json/mobile_de_database.json'
    output_path = 'data/json/mobile_de_database_no_values.json'
    remove_values_from_mobile_de(input_path, output_path)

if __name__ == "__main__":
    main() 