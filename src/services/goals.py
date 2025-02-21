from models.goal import Goal, GoalType, GoalStatus
from datetime import datetime
from typing import List


class GoalService:
    '''Сервис для работы с целями'''

    def __init__(self, db_service):
        self.db = db_service

    async def create_goal(self, user_id: int, goal_data: dict) -> Goal:
        '''Создание новой цели'''
        with self.db.get_session() as session:
            goal = Goal(
                user_id=user_id,
                title=goal_data['title'],
                goal_type=goal_data['goal_type'],
                target_value=goal_data['target_value'],
                current_value=goal_data.get('start_value', 0),
                start_value=goal_data.get('start_value', 0),
                deadline=goal_data['deadline'],
                description=goal_data.get('description', '')
            )
            session.add(goal)
            return goal

    async def update_goal_progress(self, goal_id: int, new_value: float) -> Goal:
        '''Обновление прогресса цели'''
        with self.db.get_session() as session:
            goal = session.query(Goal).filter(Goal.id == goal_id).first()
            if not goal:
                raise ValueError('Цель не найдена')
            
            goal.current_value = new_value

            #Проверяем достижение цели
            if goal.goal_type == GoalType.WEIGHT:
                # Для веса цель может быть как уменьшение, так и увеличение
                if (goal.target_value > goal.start_value and new_value >= goal.target_value) or \
                   (goal.target_value < goal.start_value and new_value <= goal.target_value):
                    goal.status = GoalStatus.COMPLETED
            else:
                if new_value >= goal.target_value:
                    goal.status = GoalStatus.COMPLETED

            return goal
    
    async def get_user_goal(self, user_id: int) -> List[Goal]:
        '''Получение всех активных целей пользователя'''
        with self.db.get_session as session:
            goals = session.query(Goal).filter(
                Goal.user_id == user_id,
                Goal.status == GoalStatus.ACTIVE
            ).all()
            return goals
        
    async def check_overdue_goals(self):
        '''Проверка просроченных целей'''
        current_date = datetime.utcnow()
        with self.db.get_session() as session:
            overdue_goals = session.query(Goal).filter(
                Goal.status == GoalStatus.ACTIVE,
                Goal.deadline < current_date
            ).all()

            for goal in overdue_goals:
                goal.status = GoalStatus.FAILED