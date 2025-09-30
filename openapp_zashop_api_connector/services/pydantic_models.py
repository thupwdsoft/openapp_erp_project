# -*- encoding: utf-8 -*-

import pydantic
from pydantic import BaseModel
from odoo.addons.pydantic import utils
from typing import List
from extendable_pydantic import ExtendableModelMeta
from datetime import datetime, date


# PYDANTIC MODELS
class OrmModel(BaseModel):
    class Config:
        orm_mode = True
        getter_dict = utils.GenericOdooGetter


class BaseParam(BaseModel):
    data: dict = {}


class CommonMany2one(OrmModel):
    id: int
    name: str


class CategoryInfo(OrmModel):
    id: int
    name: str
    image_1920: str = None


class ProductInfo(OrmModel):
    id: int
    name: str
    price: str = pydantic.Field(default=None, alias="list_price")
    categoryId: CommonMany2one = pydantic.Field(default=None, alias="categ_id")
    image_1920: str = None