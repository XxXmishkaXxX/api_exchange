#!/bin/bash

set -e  # Остановить скрипт при ошибке

echo "🚀 1. Удаляем старые скомпилированные файлы..."
find . -name "*.c" -o -name "*.so" -o -name "*.pyc" -delete

echo "⚙️ 2. Компилируем Cython код..."
python setup.py build_ext --inplace

echo "✅ Билд завершен!"

