from datetime import timedelta

import datetime

from src.models.sleep_weight import WeightRecord
from src.models.goal import GoalStatus, Goal, GoalType
from src.models.sleep_weight import SleepRecord



class SleepWeightService:
    """Сервис для работы с записями сна и веса"""
    def __init__(self, db_service):
        self.db = db_service

    async def add_weight_record(self, user_id: int, weight: float) -> WeightRecord:
        """Добавление записи о весе"""
        with self.db.get_session() as session:
            record = WeightRecord(
                user_id=user_id,
                weight=weight,
                record_date=datetime.utcnow()
            )
            session.add(record)
            
            # Обновляем прогресс цели по весу, если она есть
            goal = await self.get_active_weight_goal(user_id)
            if goal:
                goal.current_value = weight
                if (goal.target_value > goal.start_value and weight >= goal.target_value) or \
                   (goal.target_value < goal.start_value and weight <= goal.target_value):
                    goal.status = GoalStatus.COMPLETED
            
            return record

    async def get_weight_stats(self, user_id: int) -> dict:
        """Получение статистики по весу"""
        with self.db.get_session() as session:
            # Получаем последние две записи для сравнения
            last_records = session.query(WeightRecord).filter(
                WeightRecord.user_id == user_id
            ).order_by(
                WeightRecord.record_date.desc()
            ).limit(2).all()
            
            # Получаем вес на начало недели
            week_start = datetime.utcnow() - timedelta(days=datetime.utcnow().weekday())
            week_start_record = session.query(WeightRecord).filter(
                WeightRecord.user_id == user_id,
                WeightRecord.record_date >= week_start
            ).order_by(
                WeightRecord.record_date
            ).first()
            
            return {
                'current_weight': last_records[0].weight if last_records else None,
                'previous_weight': last_records[1].weight if len(last_records) > 1 else None,
                'week_start_weight': week_start_record.weight if week_start_record else None
            }

    async def start_sleep_tracking(self, user_id: int):
        """Начало отслеживания сна"""
        with self.db.get_session() as session:
            record = SleepRecord(
                user_id=user_id,
                sleep_time=datetime.utcnow(),
                wake_time=None
            )
            session.add(record)
            return record

    async def end_sleep_tracking(self, user_id: int) -> SleepRecord:
        """Завершение отслеживания сна"""
        with self.db.get_session() as session:
            # Ищем последнюю незавершенную запись
            record = session.query(SleepRecord).filter(
                SleepRecord.user_id == user_id,
                SleepRecord.wake_time == None
            ).order_by(
                SleepRecord.sleep_time.desc()
            ).first()
            
            if record:
                record.wake_time = datetime.utcnow()
                return record
            return None

    async def get_sleep_stats(self, user_id: int, days: int = 7) -> dict:
        """Получение статистики по сну"""
        start_date = datetime.utcnow() - timedelta(days=days)
        
        with self.db.get_session() as session:
            records = session.query(SleepRecord).filter(
                SleepRecord.user_id == user_id,
                SleepRecord.sleep_time >= start_date,
                SleepRecord.wake_time != None
            ).all()
            
            if not records:
                return {
                    'avg_duration': None,
                    'optimal_duration': None
                }
            
            durations = [(r.wake_time - r.sleep_time).total_seconds() / 3600 for r in records]
            avg_duration = sum(durations) / len(durations)
            
            # Определяем оптимальную продолжительность сна как медиану
            optimal_duration = sorted(durations)[len(durations) // 2]
            
            return {
                'avg_duration': avg_duration,
                'optimal_duration': optimal_duration,
                'records_count': len(records)
            }

    async def get_active_weight_goal(self, user_id: int) -> Goal:
        """Получение активной цели по весу"""
        with self.db.get_session() as session:
            goal = session.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.goal_type == GoalType.WEIGHT,
                Goal.status == GoalStatus.ACTIVE
            ).first()
            return goal