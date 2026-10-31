"""CLI: python -m price_module < examples/synthetic-price-query.json"""
import json
import sys
from .service import PriceService, DataError
def main():
    try:
        incoming=json.load(sys.stdin)
        output=PriceService().search(incoming["request"],incoming["datasets"],
                                     incoming.get("kind","BOTH"))
        print(json.dumps(output,ensure_ascii=False,indent=2))
        return 0
    except (ValueError,KeyError,DataError) as exc:
        print(json.dumps({"error":str(exc)}),file=sys.stderr)
        return 2
if __name__=="__main__":sys.exit(main())
