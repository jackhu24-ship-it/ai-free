.PHONY: all setup data charts lint pdf check clean

# 完整生產命令 (Data-Driven Doc-as-Code 閉環)
all: data charts lint pdf

setup:
	@chmod +x scripts/setup.sh scripts/build.sh 2>/dev/null || true
	@bash scripts/setup.sh 2>/dev/null || python scripts/setup.py

# 1. 執行數據驅動計算 (算暫存器、生 Typst 代碼)
data:
	@python3 scripts/compile_matrix.py 2>/dev/null || python scripts/compile_matrix.py

# 2. 生成所有工程圖 (折線圖 + 安全狀態機)
charts:
	@python3 scripts/generate_charts.py 2>/dev/null || python scripts/generate_charts.py
	@python3 scripts/generate_fsm.py 2>/dev/null || python scripts/generate_fsm.py

# 3. 靜態規範審查 (Quality Gate)
lint:
	@python3 scripts/verify_spec.py 2>/dev/null || python scripts/verify_spec.py

# 4. 編譯長青歸檔級 PDF (PDF/A-2b)
pdf:
	@chmod +x scripts/build.sh 2>/dev/null || true
	@bash scripts/build.sh 2>/dev/null || python scripts/compile_typst.py

check:
	@python3 check_standards.py 2>/dev/null || python check_standards.py

clean:
	@rm -rf dist assets/images/*.svg docs/generated_tables.typ 2>/dev/null || rmdir /s /q dist 2>nul || true
	@echo "🧹 清理完成"
