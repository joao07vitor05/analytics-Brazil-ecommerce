from src import extract, transform, load
 
 
def main():
    print("1/3 Extraindo dados brutos...")
    raw = extract.extract_all_dfs()
 
    print("2/3 Transformando dados...")
    dfs = transform.run_transform(raw)
 
    print("3/3 Carregando no PostgreSQL...")
    load.load_all(dfs)
 
    print("Pipeline concluído.")
 
 
if __name__ == "__main__":
    main()