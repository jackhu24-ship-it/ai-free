.PHONY: all setup lint charts pdf check clean

# 完整生產命令 (Quality Gate 閉環)
all: lint charts pdf

setup:
	@chmod +x scripts/setup.sh scripts/build.sh 2>/dev/null || true
	@bash scripts/setup.sh 2>/dev/null || python scripts/setup.py

lint:
	@python3 scripts/verify_spec.py 2>/dev/null || python scripts/verify_spec.py

charts:
	@python3 scripts/generate_charts.py 2>/dev/null || python scripts/generate_charts.py

pdf:
	@chmod +x scripts/build.sh 2>/dev/null || true
	@bash scripts/build.sh 2>/dev/null || python scripts/compile_typst.py

check:
	@python3 check_standards.py 2>/dev/null || python check_standards.py

clean:
	@rm -rf dist assets/images/*.svg 2>/dev/null || rmdir /s /q dist 2>nul || true
	@echo "🧹 清理完畢"
