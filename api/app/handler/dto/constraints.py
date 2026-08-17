from typing import Annotated

from pydantic import StringConstraints


String50 = Annotated[str, StringConstraints(max_length=50)]
String100 = Annotated[str, StringConstraints(max_length=100)]
String255 = Annotated[str, StringConstraints(max_length=255)]
String500 = Annotated[str, StringConstraints(max_length=500)]
PasswordString = Annotated[str, StringConstraints(min_length=8, max_length=255)]
TokenString = Annotated[str, StringConstraints(min_length=1, max_length=500)]
