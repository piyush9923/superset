# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from typing import Any

from flask_babel import lazy_gettext as _
from sqlalchemy import and_, or_
from sqlalchemy.orm.query import Query

from superset import db, security_manager
from superset.connectors.sqla import models
from superset.connectors.sqla.models import SqlaTable
from superset.models.slice import Slice
from superset.utils.core import get_user_id
from superset.views.base import BaseFilter
from superset.views.base_api import BaseFavoriteFilter, BaseTagFilter


class ChartAllTextFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    name = _("All Text")
    arg_name = "chart_all_text"

    def apply(self, query: Query, value: Any) -> Query:
        if not value:
            return query
        ilike_value = f"%{value}%"
        return query.filter(
            or_(
                Slice.slice_name.ilike(ilike_value),
                Slice.description.ilike(ilike_value),
                Slice.viz_type.ilike(ilike_value),
                SqlaTable.table_name.ilike(ilike_value),
            )
        )


class ChartFavoriteFilter(BaseFavoriteFilter):  # pylint: disable=too-few-public-methods
    """
    Custom filter for the GET list that filters all charts that a user has favored
    """

    arg_name = "chart_is_favorite"
    class_name = "slice"
    model = Slice


class ChartTagFilter(BaseTagFilter):  # pylint: disable=too-few-public-methods
    """
    Custom filter for the GET list that filters all dashboards that a user has favored
    """

    arg_name = "chart_tags"
    class_name = "slice"
    model = Slice


class ChartCertifiedFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    """
    Custom filter for the GET list that filters all certified charts
    """

    name = _("Is certified")
    arg_name = "chart_is_certified"

    def apply(self, query: Query, value: Any) -> Query:
        if value is True:
            return query.filter(and_(Slice.certified_by.isnot(None)))
        if value is False:
            return query.filter(and_(Slice.certified_by.is_(None)))
        return query


class ChartFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    def apply(self, query: Query, value: Any) -> Query:
        if security_manager.can_access_all_datasources():
            return query
        perms = security_manager.user_view_menu_names("datasource_access")
        schema_perms = security_manager.user_view_menu_names("schema_access")
        owner_ids_query = (
            db.session.query(models.SqlaTable.id)
            .join(models.SqlaTable.owners)
            .filter(
                security_manager.user_model.id
                == security_manager.user_model.get_user_id()
            )
        )
        return query.filter(
            or_(
                self.model.perm.in_(perms),
                self.model.schema_perm.in_(schema_perms),
                models.SqlaTable.id.in_(owner_ids_query),
            )
        )


class ChartHasCreatedByFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    """
    Custom filter for the GET list that filters all charts created by user
    """

    name = _("Has created by")
    arg_name = "chart_has_created_by"

    def apply(self, query: Query, value: Any) -> Query:
        if value is True:
            return query.filter(and_(Slice.created_by_fk.isnot(None)))
        if value is False:
            return query.filter(and_(Slice.created_by_fk.is_(None)))
        return query


class ChartCreatedByMeFilter(BaseFilter):  # pylint: disable=too-few-public-methods
    name = _("Created by me")
    arg_name = "chart_created_by_me"

    def apply(self, query: Query, value: Any) -> Query:
        return query.filter(
            or_(
                Slice.created_by_fk  # pylint: disable=comparison-with-callable
                == get_user_id(),
                Slice.changed_by_fk  # pylint: disable=comparison-with-callable
                == get_user_id(),
            )
        )
