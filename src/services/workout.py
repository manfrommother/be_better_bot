from datetime import datetime, timedelta
from typing import List, Dict, Optional
from sqlalchemy import func
from sqlalchemy import distinct

from src.models.workout import Exercise


class ExerciseService:
   """Сервис для работы с тренировками"""
   def __init__(self, db_service):
       self.db = db_service

   async def add_exercise(
       self,
       user_id: int,
       name: str,
       weight: float,
       reps: int,
       sets: int,
       workout_date: datetime
   ) -> Exercise:
       """
       Добавление нового упражнения
       
       :param user_id: ID пользователя
       :param name: Название упражнения
       :param weight: Вес в кг
       :param reps: Количество повторений
       :param sets: Количество подходов
       :param workout_date: Дата тренировки
       :return: Созданная запись упражнения
       """
       with self.db.get_session() as session:
           exercise = Exercise(
               user_id=user_id,
               name=name.strip().lower(),  # Нормализуем название
               weight=weight,
               reps=reps,
               sets=sets,
               workout_date=workout_date
           )
           session.add(exercise)
           return exercise

   async def get_exercise_stats(
       self,
       user_id: int,
       exercise_name: str
   ) -> Dict:
       """
       Получение статистики по конкретному упражнению
       
       :param user_id: ID пользователя
       :param exercise_name: Название упражнения
       :return: Словарь со статистикой
       """
       with self.db.get_session() as session:
           # Нормализуем название упражнения
           exercise_name = exercise_name.strip().lower()
           
           # Получаем последнюю запись перед текущей
           prev_exercise = session.query(Exercise).filter(
               Exercise.user_id == user_id,
               Exercise.name == exercise_name,
               Exercise.workout_date < datetime.utcnow()
           ).order_by(
               Exercise.workout_date.desc()
           ).first()
           
           # Получаем максимальный вес
           max_weight = session.query(func.max(Exercise.weight)).filter(
               Exercise.user_id == user_id,
               Exercise.name == exercise_name
           ).scalar()
           
           # Получаем среднее количество повторений
           avg_reps = session.query(func.avg(Exercise.reps)).filter(
               Exercise.user_id == user_id,
               Exercise.name == exercise_name
           ).scalar()
           
           return {
               'prev_weight': prev_exercise.weight if prev_exercise else None,
               'max_weight': max_weight,
               'avg_reps': round(avg_reps) if avg_reps else None
           }

   async def get_user_stats(self, user_id: int) -> Dict:
       """
       Получение общей статистики пользователя по тренировкам
       
       :param user_id: ID пользователя
       :return: Словарь со статистикой
       """
       with self.db.get_session() as session:
           # Последние упражнения
           recent_exercises = session.query(Exercise).filter(
               Exercise.user_id == user_id
           ).order_by(
               Exercise.workout_date.desc()
           ).limit(5).all()
           
           # Максимальные веса по каждому упражнению
           max_weights_query = session.query(
               Exercise.name,
               func.max(Exercise.weight).label('max_weight')
           ).filter(
               Exercise.user_id == user_id
           ).group_by(
               Exercise.name
           ).all()
           
           max_weights = {ex.name: weight for ex, weight in max_weights_query}
           
           # Количество тренировок за последний месяц
           month_ago = datetime.utcnow() - timedelta(days=30)
           workouts_count = session.query(
               func.count(distinct(Exercise.workout_date))
           ).filter(
               Exercise.user_id == user_id,
               Exercise.workout_date >= month_ago
           ).scalar()
           
           return {
               'recent_exercises': recent_exercises,
               'max_weights': max_weights,
               'workouts_last_month': workouts_count
           }

   async def get_user_history(
       self,
       user_id: int,
       days: int = None,
       limit: int = None
   ) -> List[Exercise]:
       """
       Получение истории тренировок пользователя
       
       :param user_id: ID пользователя
       :param days: Количество дней для выборки (опционально)
       :param limit: Ограничение количества записей (опционально)
       :return: Список упражнений
       """
       with self.db.get_session() as session:
           query = session.query(Exercise).filter(
               Exercise.user_id == user_id
           )
           
           if days:
               start_date = datetime.utcnow() - timedelta(days=days)
               query = query.filter(Exercise.workout_date >= start_date)
           
           query = query.order_by(Exercise.workout_date.desc())
           
           if limit:
               query = query.limit(limit)
           
           return query.all()

   async def get_exercise_progress(
       self,
       user_id: int,
       exercise_name: str,
       days: int = 30
   ) -> List[Dict]:
       """
       Получение прогресса по конкретному упражнению
       
       :param user_id: ID пользователя
       :param exercise_name: Название упражнения
       :param days: Количество дней для анализа
       :return: Список с данными о прогрессе
       """
       with self.db.get_session() as session:
           start_date = datetime.utcnow() - timedelta(days=days)
           
           exercises = session.query(Exercise).filter(
               Exercise.user_id == user_id,
               Exercise.name == exercise_name.strip().lower(),
               Exercise.workout_date >= start_date
           ).order_by(
               Exercise.workout_date
           ).all()
           
           progress = []
           for exercise in exercises:
               progress.append({
                   'date': exercise.workout_date.strftime('%d.%m.%Y'),
                   'weight': exercise.weight,
                   'reps': exercise.reps,
                   'sets': exercise.sets,
                   'total_volume': exercise.weight * exercise.reps * exercise.sets
               })
           
           return progress

   async def get_user_top_exercises(
       self,
       user_id: int,
       limit: int = 5
   ) -> List[Dict]:
       """
       Получение топ упражнений пользователя по максимальному весу
       
       :param user_id: ID пользователя
       :param limit: Количество упражнений
       :return: Список топ упражнений
       """
       with self.db.get_session() as session:
           top_exercises = session.query(
               Exercise.name,
               func.max(Exercise.weight).label('max_weight'),
               func.count(Exercise.id).label('total_sets')
           ).filter(
               Exercise.user_id == user_id
           ).group_by(
               Exercise.name
           ).order_by(
               func.max(Exercise.weight).desc()
           ).limit(limit).all()
           
           return [
               {
                   'name': exercise.name,
                   'max_weight': exercise.max_weight,
                   'total_sets': exercise.total_sets
               }
               for exercise in top_exercises
           ]