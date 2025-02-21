from datetime import datetime, timedelta
from sqlalchemy import func, Transaction
from models.analytics import UserActivity
from models.workout import Exercise
from models.sleep_weight import SleepRecord
from models.goal import Goal, GoalStatus


class AnalyticsService:
    """
    Сервис для сбора и анализа статистики использования бота
    """
    def __init__(self, db_service):
        self.db = db_service

    async def collect_user_activity(self, user_id: int, action: str):
        """
        Сохранение информации о действиях пользователя
        
        :param user_id: ID пользователя
        :param action: Выполненное действие
        """
        with self.db.get_session() as session:
            activity = UserActivity(
                user_id=user_id,
                action=action,
                timestamp=datetime.utcnow()
            )
            session.add(activity)

    async def get_user_statistics(self, user_id: int, days: int = 7):
        """
        Получение статистики использования бота пользователем
        
        :param user_id: ID пользователя
        :param days: Количество дней для анализа
        :return: Словарь со статистикой
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        with self.db.get_session() as session:
            stats = {
                'total_transactions': session.query(Transaction)
                    .filter(Transaction.user_id == user_id)
                    .filter(Transaction.created_at >= start_date)
                    .count(),
                'total_workouts': session.query(Exercise)
                    .filter(Exercise.user_id == user_id)
                    .filter(Exercise.created_at >= start_date)
                    .count(),
                'sleep_records': session.query(SleepRecord)
                    .filter(SleepRecord.user_id == user_id)
                    .filter(SleepRecord.created_at >= start_date)
                    .count(),
                'active_goals': session.query(Goal)
                    .filter(Goal.user_id == user_id)
                    .filter(Goal.status == GoalStatus.ACTIVE)
                    .count()
            }
            
            return stats

    async def get_popular_features(self, days: int = 7):
        """
        Получение статистики по популярности различных функций бота
        
        :param days: Количество дней для анализа
        :return: Словарь с статистикой использования функций
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        with self.db.get_session() as session:
            activities = session.query(
                UserActivity.action,
                func.count(UserActivity.id).label('count')
            ).filter(
                UserActivity.timestamp >= start_date
            ).group_by(
                UserActivity.action
            ).order_by(
                func.count(UserActivity.id).desc()
            ).all()
            
            return {activity.action: activity.count for activity in activities}
