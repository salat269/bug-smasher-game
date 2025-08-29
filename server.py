#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Хранит общий лидерборд для всех игроков
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import json
import sqlite3
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для всех доменов

# Создаем базу данных
def init_db():
    conn = sqlite3.connect('leaderboard.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            player_name TEXT NOT NULL,
            score INTEGER NOT NULL,
            bugs INTEGER NOT NULL,
            max_combo INTEGER NOT NULL,
            date TEXT NOT NULL,
            telegram_user_id TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Инициализируем БД при запуске
init_db()

@app.route('/')
def index():
    """Главная страница с игрой"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Bug Smasher Game - Server</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        <h1>🐛 Bug Smasher Game Server</h1>
        <p>Сервер работает! Игра доступна по адресу:</p>
        <p><strong>https://YOUR_USERNAME.github.io/bug-smasher-game/</strong></p>
        <hr>
        <h2>📊 API Endpoints:</h2>
        <ul>
            <li><code>GET /api/leaderboard</code> - Получить лидерборд</li>
            <li><code>POST /api/score</code> - Сохранить результат</li>
            <li><code>GET /api/stats</code> - Статистика сервера</li>
        </ul>
    </body>
    </html>
    ''')

@app.route('/api/leaderboard')
def get_leaderboard():
    """Получить топ-15 игроков"""
    try:
        conn = sqlite3.connect('leaderboard.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT player_name, score, bugs, max_combo, date, telegram_user_id
            FROM leaderboard 
            ORDER BY score DESC 
            LIMIT 15
        ''')
        results = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for row in results:
            leaderboard.append({
                'player_name': row[0],
                'score': row[1],
                'bugs': row[2],
                'max_combo': row[3],
                'date': row[4],
                'telegram_user_id': row[5]
            })
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard,
            'total_records': len(leaderboard)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/score', methods=['POST'])
def save_score():
    """Сохранить результат игры"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        player_name = data.get('playerName', 'Anonymous')
        score = data.get('score', 0)
        bugs = data.get('bugs', 0)
        max_combo = data.get('maxCombo', 1)
        telegram_user_id = data.get('telegramUserId')
        
        # Валидация данных
        if not isinstance(score, int) or score < 0:
            return jsonify({'success': False, 'error': 'Invalid score'}), 400
        
        if not isinstance(bugs, int) or bugs < 0:
            return jsonify({'success': False, 'error': 'Invalid bugs count'}), 400
        
        # Сохраняем в базу
        conn = sqlite3.connect('leaderboard.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO leaderboard (player_name, score, bugs, max_combo, date, telegram_user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (player_name, score, bugs, max_combo, datetime.now().strftime('%d.%m.%Y %H:%M'), telegram_user_id))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Score saved successfully',
            'player_name': player_name,
            'score': score
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/stats')
def get_stats():
    """Получить статистику сервера"""
    try:
        conn = sqlite3.connect('leaderboard.db')
        cursor = conn.cursor()
        
        # Общее количество записей
        cursor.execute('SELECT COUNT(*) FROM leaderboard')
        total_records = cursor.fetchone()[0]
        
        # Средний счет
        cursor.execute('SELECT AVG(score) FROM leaderboard')
        avg_score = cursor.fetchone()[0] or 0
        
        # Максимальный счет
        cursor.execute('SELECT MAX(score) FROM leaderboard')
        max_score = cursor.fetchone()[0] or 0
        
        # Количество уникальных игроков
        cursor.execute('SELECT COUNT(DISTINCT player_name) FROM leaderboard')
        unique_players = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_records': total_records,
                'average_score': round(avg_score, 2),
                'max_score': max_score,
                'unique_players': unique_players,
                'server_time': datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/player/<player_name>')
def get_player_stats(player_name):
    """Получить статистику конкретного игрока"""
    try:
        conn = sqlite3.connect('leaderboard.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT score, bugs, max_combo, date
            FROM leaderboard 
            WHERE player_name = ?
            ORDER BY score DESC
        ''', (player_name,))
        results = cursor.fetchall()
        
        conn.close()
        
        if not results:
            return jsonify({
                'success': False,
                'error': 'Player not found'
            }), 404
        
        player_stats = []
        for row in results:
            player_stats.append({
                'score': row[0],
                'bugs': row[1],
                'max_combo': row[2],
                'date': row[3]
            })
        
        best_score = max(player_stats, key=lambda x: x['score'])
        
        return jsonify({
            'success': True,
            'player_name': player_name,
            'best_score': best_score,
            'total_games': len(player_stats),
            'all_scores': player_stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("🚀 Bug Smasher Game Server запущен!")
    print("📊 API доступен по адресу: http://localhost:5000")
    print("📋 Endpoints:")
    print("   GET  /api/leaderboard - Получить лидерборд")
    print("   POST /api/score - Сохранить результат")
    print("   GET  /api/stats - Статистика сервера")
    print("   GET  /api/player/<name> - Статистика игрока")
    print("\n🛑 Для остановки нажмите Ctrl+C")
    
    # Получаем порт из переменной окружения (для Railway/Heroku)
    port = int(os.environ.get('PORT', 5000))
    
    # Запускаем в продакшен режиме
    app.run(host='0.0.0.0', port=port, debug=False)
