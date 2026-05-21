from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DoctorSignup(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    subject_name: str = Field(min_length=2, max_length=255)


class DoctorLogin(BaseModel):
    email: EmailStr
    password: str
    remember_me: bool = True


class StudentCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr | None = None


class StudentUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=150)
    email: EmailStr | None = None


class ComponentCreate(BaseModel):
    label: str = Field(min_length=2, max_length=120)
    semester: int = Field(ge=1, le=2)
    category: str = Field(pattern="^(coursework|final)$")
    max_score: float = Field(gt=0)
    order_index: int = 0


class ComponentUpdate(BaseModel):
    label: str = Field(min_length=2, max_length=120)
    semester: int = Field(ge=1, le=2)
    category: str = Field(pattern="^(coursework|final)$")
    max_score: float = Field(gt=0)
    order_index: int = 0


class GradingPolicyUpdate(BaseModel):
    coursework_total_max: float = Field(gt=0, le=200)


class ScorePatch(BaseModel):
    scores: dict[str, float]


class PublishRequest(BaseModel):
    component_keys: list[str] = Field(default_factory=list)
    student_ids: list[int] | None = None
    send_email: bool = False
    force_new_token: bool = False
    semester: int = Field(ge=1, le=2, default=1)


class StudentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str | None


class ComponentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    component_key: str
    label: str
    semester: int
    category: str
    max_score: float
    order_index: int
