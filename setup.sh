#!/bin/bash
# ============================================================
# SETUP SCRIPT - Billar Manager
# Ejecuta esto UNA sola vez para preparar el entorno completo
# ============================================================

set -e  # Detener si algún comando falla

echo "🎱 Iniciando setup de Billar Manager..."

# 1. Crear entorno virtual
echo "📦 Creando entorno virtual..."
python3 -m venv venv

# 2. Activar entorno virtual
source venv/bin/activate

# 3. Instalar dependencias
echo "⬇️  Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Copiar variables de entorno
if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚙️  Archivo .env creado. Edítalo antes de continuar."
fi

# 5. Migraciones
echo "🗄️  Aplicando migraciones..."
python manage.py migrate

# 6. Crear superusuario (opcional)
echo ""
echo "¿Deseas crear un superusuario ahora? (s/n)"
read -r CREATE_SUPER
if [ "$CREATE_SUPER" = "s" ]; then
    python manage.py createsuperuser
fi

echo ""
echo "✅ Setup completado."
echo "👉 Para iniciar el servidor:"
echo "   source venv/bin/activate"
echo "   python manage.py runserver"
