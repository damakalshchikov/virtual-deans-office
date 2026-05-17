"""Вспомогательные функции системы."""
from models import db, Notification, StudentKompetenciya, VacancyRequirement


def notify(user_id, message, link=None):
    """Создать уведомление для пользователя."""
    n = Notification(user_id=user_id, message=message, link=link)
    db.session.add(n)
    db.session.commit()


def calc_match(student_id, vacancy_id):
    """Расчёт процента совпадения компетенций студента и требований вакансии."""
    reqs = VacancyRequirement.query.filter_by(vacancy_id=vacancy_id).all()
    if not reqs:
        return 100  # нет требований — 100% совпадение

    student_komps = {sk.kompetenciya_id: sk.level
                     for sk in StudentKompetenciya.query.filter_by(student_id=student_id).all()}

    matched = 0
    for req in reqs:
        student_level = student_komps.get(req.kompetenciya_id, 0)
        if student_level >= req.min_level:
            matched += 1

    return int(matched / len(reqs) * 100)
