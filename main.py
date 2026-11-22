from src import extract, transform, load
from src.gold import load_gold
 
 
def main():
    print("1/3 Extraindo dados brutos...")
    raw = extract.extract_all_dfs()
 
    print("2/3 Transformando dados...")
    dfs = transform.run_transform(raw)
 
    print("3/3 Carregando no PostgreSQL...")
    load.load_all(dfs)

    print("\n4/4 Construindo e carregando a camada Gold...")
    load_gold.main()

    print("\nPipeline completo: Silver e Gold carregadas com sucesso!")
 
    
 
 
if __name__ == "__main__":
    main()