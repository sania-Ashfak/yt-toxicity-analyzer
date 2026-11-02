"""Pipeline runner:  python main.py [extract|transform|load|eda|all]"""
import sys
import config

def all_pipeline():
    import extract;  extract.run()
    import transform, load
    load.run(transform.run())
    import eda;      eda.run()

if __name__ == "__main__":
    step = sys.argv[1] if len(sys.argv) > 1 else "all"
    if step == "extract":
        import extract; extract.run()
    elif step == "transform":
        import transform; transform.run()
    elif step == "load":
        import transform, load; load.run(transform.run())
    elif step == "eda":
        import eda; eda.run()
    elif step == "all":
        all_pipeline()
    else:
        sys.exit(f"Unknown step: {step}")
