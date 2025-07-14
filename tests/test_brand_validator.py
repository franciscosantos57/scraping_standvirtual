#!/usr/bin/env python3
"""
Script de teste para o validador de marcas e modelos
"""

from utils.brand_model_validator import validator


def test_basic_functionality():
    """Testa funcionalidades básicas do validador"""
    print("🧪 Testando funcionalidades básicas...")
    print("="*50)
    
    # Estatísticas
    stats = validator.get_stats()
    print(f"📊 Estatísticas:")
    print(f"   Marcas: {stats['total_brands']}")
    print(f"   Modelos: {stats['total_models']}")
    print(f"   Média modelos/marca: {stats['avg_models_per_brand']}")
    
    # Lista de marcas
    brands = validator.get_all_brands()
    print(f"\n📋 Marcas disponíveis ({len(brands)}):")
    for i, brand in enumerate(brands[:10], 1):
        print(f"   {i:2d}. {brand}")
    if len(brands) > 10:
        print(f"   ... e mais {len(brands) - 10} marcas")


def test_brand_validation():
    """Testa validação de marcas"""
    print(f"\n🔍 Testando validação de marcas...")
    print("-"*30)
    
    test_brands = ["BMW", "Audi", "Tesla", "Marca Inexistente", "mercedes-benz"]
    
    for brand in test_brands:
        is_valid = validator.is_valid_brand(brand)
        status = "✅ Válida" if is_valid else "❌ Inválida"
        print(f"   {brand}: {status}")
        
        if not is_valid:
            suggestions = validator.suggest_brands(brand)
            if suggestions:
                print(f"      💡 Sugestões: {suggestions}")


def test_model_validation():
    """Testa validação de modelos"""
    print(f"\n🚗 Testando validação de modelos...")
    print("-"*30)
    
    test_cases = [
        ("BMW", "X5"),
        ("BMW", "Serie 3"),
        ("BMW", "Modelo Inexistente"),
        ("Audi", "A4"),
        ("Audi", "Q7"),
        ("Mercedes-Benz", "Classe C"),
        ("Toyota", "Corolla"),
        ("Ford", "Focus")
    ]
    
    for brand, model in test_cases:
        if validator.is_valid_brand(brand):
            is_valid = validator.is_valid_model(brand, model)
            status = "✅ Válido" if is_valid else "❌ Inválido"
            print(f"   {brand} {model}: {status}")
            
            if not is_valid:
                suggestions = validator.suggest_models(brand, model)
                if suggestions:
                    suggested_names = [s['text'] for s in suggestions[:3]]
                    print(f"      💡 Sugestões: {suggested_names}")


def test_search_params_validation():
    """Testa validação completa de parâmetros de pesquisa"""
    print(f"\n🔧 Testando validação de parâmetros de pesquisa...")
    print("-"*40)
    
    test_cases = [
        ("BMW", "X5"),
        ("BMW", "Modelo Inexistente"),
        ("Marca Inexistente", "Modelo"),
        ("Audi", "R8"),
        ("", ""),
    ]
    
    for brand, model in test_cases:
        print(f"\n📝 Testando: Marca='{brand}', Modelo='{model}'")
        result = validator.validate_search_params(brand, model)
        
        if result['valid']:
            print(f"   ✅ Parâmetros válidos")
            if result['brand_value']:
                print(f"      brand_value: {result['brand_value']}")
            if result['model_value']:
                print(f"      model_value: {result['model_value']}")
        else:
            print(f"   ❌ Parâmetros inválidos")
            for error in result['errors']:
                print(f"      ⚠️ {error}")
            
            if result['suggestions']:
                for key, suggestions in result['suggestions'].items():
                    print(f"      💡 {key}: {suggestions}")


def test_models_for_brands():
    """Testa obtenção de modelos para marcas específicas"""
    print(f"\n🏷️ Testando modelos por marca...")
    print("-"*30)
    
    test_brands = ["BMW", "Audi", "Toyota"]
    
    for brand in test_brands:
        models = validator.get_models_for_brand(brand)
        print(f"\n{brand}: {len(models)} modelos")
        
        # Mostra primeiros 5 modelos
        for i, model in enumerate(models[:5], 1):
            print(f"   {i}. {model['text']} (value: {model['value']})")
        
        if len(models) > 5:
            print(f"   ... e mais {len(models) - 5} modelos")


def test_suggestions():
    """Testa sistema de sugestões"""
    print(f"\n💡 Testando sistema de sugestões...")
    print("-"*30)
    
    # Sugestões de marcas
    partial_brands = ["BM", "Mer", "Au", "Vol"]
    
    print("Sugestões de marcas:")
    for partial in partial_brands:
        suggestions = validator.suggest_brands(partial)
        print(f"   '{partial}' → {suggestions}")
    
    # Sugestões de modelos
    print(f"\nSugestões de modelos:")
    model_tests = [
        ("BMW", "X"),
        ("BMW", "Serie"),
        ("Audi", "A"),
        ("Mercedes-Benz", "Classe")
    ]
    
    for brand, partial in model_tests:
        suggestions = validator.suggest_models(brand, partial)
        suggestion_names = [s['text'] for s in suggestions[:5]]
        print(f"   {brand} '{partial}' → {suggestion_names}")


def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes do validador de marcas e modelos...")
    print("="*60)
    
    try:
        test_basic_functionality()
        test_brand_validation()
        test_model_validation()
        test_search_params_validation()
        test_models_for_brands()
        test_suggestions()
        
        print(f"\n✅ Todos os testes concluídos!")
        print(f"\n💡 Como usar no seu código:")
        print(f"   from utils.brand_model_validator import validator")
        print(f"   brands = validator.get_all_brands()")
        print(f"   models = validator.get_models_for_brand('BMW')")
        print(f"   result = validator.validate_search_params('BMW', 'X5')")
        
    except Exception as e:
        print(f"❌ Erro durante os testes: {e}")


if __name__ == "__main__":
    main() 