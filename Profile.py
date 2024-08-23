class Profile:
    def __init__(self, data: []) -> None:
        self.user_id: int = int(data[0])
        if len(data) == 1:
            self.stage: int = 0
            self.name: str = ""
            self.age: int = 0
            self.photos = ""
            self.raw_photos = []
            self.desc: str = ""
            self.sex: int = 0
            return
        self.stage: int = -1
        self.name: str = data[1]
        self.age: int = int(data[2])
        self.photos = data[3]
        self.raw_photos = data[3].split(';')
        self.desc: str = data[4]
        self.sex: int = int(data[5])

    def get_text(self) -> str:
        text = f"{self.name}, {self.age}"
        if len(self.desc) != 0:
            text += f" – {self.desc}"
        return text

    def get_sqlparams(self) -> tuple:
        return self.name, int(self.age), self.photos, self.desc, int(self.sex), self.user_id

    def validate_age(self, age: str) -> None:
        try:
            age = int(age)
        except ValueError:
            raise RuntimeError("Укажите только число")
        if not 8 <= age <= 99:
            raise RuntimeError("Укажите адекватный возраст")
        self.age = int(age)

    def validate_name(self, name: str) -> None:
        if not 2 < len(name) <= 15:
            raise RuntimeError("Длина имени от 3 до 15 символов")
        self.name = name

    def validate_descr(self, desc: str) -> None:
        if len(desc) > 1000:
            raise RuntimeError("Описание должно быть меньше 1000 символов")
        self.desc = desc

    def validate_sex(self, sex: str) -> None:
        if sex not in ["Я девушка", "Я парень"]:
            raise RuntimeError("Нет такого варианта ответа")
        self.sex = (sex == "Я девушка")
