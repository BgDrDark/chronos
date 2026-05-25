import datetime
import logging
from datetime import timedelta
from decimal import Decimal

import strawberry
from sqlalchemy import select

from backend.database import models
from backend.database.models import sofia_now
from backend.database.transaction_manager import atomic_transaction
from backend.exceptions import (
    AuthenticationException,
    PermissionDeniedException,
    ValidationException,
)
from backend.graphql import inputs, types
from backend.services.recipe_cost_calculator import RecipeCostCalculator

logger = logging.getLogger(__name__)
authenticate_msg = "Трябва да се автентикирате"


@strawberry.type
class ProductionMutation:

    @strawberry.mutation
    async def create_recipe(self, input: inputs.RecipeInput, info: strawberry.Info) -> types.Recipe:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            Company,
            Recipe,
            RecipeIngredient,
            RecipeSection,
            RecipeStep,
        )

        company = await db.get(Company, input.company_id)
        if not company:
            raise PermissionDeniedException.for_action("manage recipes")
        if current_user.role.name not in ["admin", "super_admin"] and company.id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage recipes")

        recipe = Recipe(
            name=input.name, description=input.description,
            yield_quantity=input.yield_quantity, yield_unit=input.yield_unit,
            shelf_life_days=input.shelf_life_days,
            shelf_life_frozen_days=input.shelf_life_frozen_days,
            default_pieces=input.default_pieces,
            production_time_days=input.production_time_days,
            standard_quantity=input.standard_quantity,
            instructions=input.instructions, company_id=input.company_id,
        )
        db.add(recipe)
        await db.flush()

        for section_input in input.sections:
            section = RecipeSection(
                recipe_id=recipe.id, section_type=section_input.section_type,
                name=section_input.name, shelf_life_days=section_input.shelf_life_days,
                waste_percentage=float(section_input.waste_percentage),
                section_order=section_input.section_order,
            )
            db.add(section)
            await db.flush()

            for ing_input in section_input.ingredients:
                ri = RecipeIngredient(
                    recipe_id=recipe.id, section_id=section.id,
                    ingredient_id=ing_input.ingredient_id,
                    quantity_gross=ing_input.quantity_gross,
                    quantity_net=ing_input.quantity_net,
                    waste_percentage=ing_input.waste_percentage,
                    workstation_id=ing_input.workstation_id,
                )
                db.add(ri)

            for step_input in section_input.steps:
                rs = RecipeStep(
                    section_id=section.id, recipe_id=recipe.id,
                    workstation_id=step_input.workstation_id,
                    name=step_input.name, step_order=step_input.step_order,
                    estimated_duration_minutes=step_input.estimated_duration_minutes,
                )
                db.add(rs)

        for ing_input in input.ingredients:
            ri = RecipeIngredient(
                recipe_id=recipe.id, ingredient_id=ing_input.ingredient_id,
                quantity_gross=ing_input.quantity_gross,
                quantity_net=ing_input.quantity_net,
                waste_percentage=ing_input.waste_percentage,
                workstation_id=ing_input.workstation_id,
            )
            db.add(ri)

        for step_input in input.steps:
            rs = RecipeStep(
                recipe_id=recipe.id, workstation_id=step_input.workstation_id,
                name=step_input.name, step_order=step_input.step_order,
                estimated_duration_minutes=step_input.estimated_duration_minutes,
            )
            db.add(rs)

        await db.commit()
        await db.refresh(recipe)
        return types.Recipe.from_pydantic(recipe)

    @strawberry.mutation
    async def delete_recipe(self, id: int, info: strawberry.Info) -> bool:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Recipe

        recipe = await db.get(Recipe, id)
        if not recipe:
            raise ValidationException(detail="Рецептата не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and recipe.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage recipes")

        await db.delete(recipe)
        await db.commit()
        return True

    @strawberry.mutation
    async def update_recipe_price(
            self, recipe_id: int, input: inputs.RecipePriceUpdateInput,
            info: strawberry.Info,
    ) -> types.Recipe:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Recipe

        recipe = await db.get(Recipe, recipe_id)
        if not recipe:
            raise ValidationException(detail="Рецептата не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and recipe.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage recipes")

        calculator = RecipeCostCalculator(db)
        await calculator.update_price(recipe, input)
        await db.commit()
        await db.refresh(recipe)
        return types.Recipe.from_pydantic(recipe)

    @strawberry.mutation
    async def calculate_recipe_cost(self, recipe_id: int, info: strawberry.Info) -> types.RecipeCostResult:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        calculator = RecipeCostCalculator(db)
        result = await calculator.calculate_cost(recipe_id)
        return types.RecipeCostResult(
            recipe_id=result["recipe_id"],
            recipe_name=result["recipe_name"],
            cost_price=result["cost_price"],
            markup_amount=result["markup_amount"],
            premium_amount=result["premium_amount"],
            final_price=result["final_price"],
            portion_price=result["portion_price"],
        )

    @strawberry.mutation
    async def recalculate_all_recipe_costs(self, info: strawberry.Info) -> list[types.RecalculateResult]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        calculator = RecipeCostCalculator(db)
        results = await calculator.recalculate_all()
        return [
            types.RecalculateResult(
                recipe_id=r["recipe_id"],
                recipe_name=r["recipe_name"],
                cost_price=r["cost_price"],
                markup_amount=r["markup_amount"],
                final_price=r["final_price"],
                portion_price=r["portion_price"],
            )
            for r in results
        ]

    @strawberry.mutation
    async def create_workstation(
            self, name: str, description: str | None, company_id: int,
            info: strawberry.Info,
    ) -> types.Workstation:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import Company, Workstation

        company = await db.get(Company, company_id)
        if not company:
            raise PermissionDeniedException.for_action("manage workstations")
        if current_user.role.name not in ["admin", "super_admin"] and company.id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage workstations")

        ws = Workstation(name=name, description=description, company_id=company_id)
        db.add(ws)
        await db.commit()
        await db.refresh(ws)
        return types.Workstation.from_pydantic(ws)

    @strawberry.mutation
    async def create_production_order(
            self, input: inputs.ProductionOrderInput,
            info: strawberry.Info,
    ) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            Company,
            ProductionOrder,
            ProductionTask,
            Recipe,
        )

        company = await db.get(Company, input.company_id)
        if not company:
            raise PermissionDeniedException.for_action("manage production orders")
        if current_user.role.name not in ["admin", "super_admin"] and company.id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage production orders")

        recipe = await db.get(Recipe, input.recipe_id)
        if not recipe:
            raise ValidationException(detail="Рецептата не съществува")

        async with atomic_transaction(db):
            order = ProductionOrder(
                recipe_id=input.recipe_id, quantity=input.quantity,
                due_date=input.due_date, notes=input.notes,
                company_id=input.company_id,
                status="pending",
                created_by=current_user.id,
                created_at=datetime.datetime.now(),
                production_deadline=input.due_date - timedelta(days=recipe.production_time_days or 1),
            )
            db.add(order)
            await db.flush()

            recipe_stmt = select(models.RecipeSection).where(models.RecipeSection.recipe_id == input.recipe_id)
            recipe_res = await db.execute(recipe_stmt)
            sections = recipe_res.scalars().all()

            if sections:
                for section in sections:
                    step_stmt = select(models.RecipeStep).where(models.RecipeStep.section_id == section.id)
                    step_res = await db.execute(step_stmt)
                    for step in step_res.scalars().all():
                        task = ProductionTask(
                            order_id=order.id, workstation_id=step.workstation_id,
                            step_id=step.id, name=step.name,
                            status="pending", assigned_user_id=None,
                        )
                        db.add(task)
            else:
                step_stmt = select(models.RecipeStep).where(models.RecipeStep.recipe_id == input.recipe_id)
                step_res = await db.execute(step_stmt)
                for step in step_res.scalars().all():
                    task = ProductionTask(
                        order_id=order.id, workstation_id=step.workstation_id,
                        step_id=step.id, name=step.name,
                        status="pending", assigned_user_id=None,
                    )
                    db.add(task)

        await db.refresh(order)
        return types.ProductionOrder.from_pydantic(order)

    @strawberry.mutation
    async def update_production_order_status(
            self, id: int, status: str, info: strawberry.Info,
    ) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder

        order = await db.get(ProductionOrder, id)
        if not order:
            raise ValidationException(detail="Поръчката не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage production orders")

        order.status = status
        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_pydantic(order)

    @strawberry.mutation
    async def confirm_production_order(self, id: int, info: strawberry.Info) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            ProductionOrder,
            ProductionRecord,
            ProductionRecordIngredient,
            ProductionRecordWorker,
            ProductionTask,
            Recipe,
        )

        order = await db.get(ProductionOrder, id)
        if not order:
            raise ValidationException(detail="Поръчката не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("confirm production orders")

        recipe = await db.get(Recipe, order.recipe_id)
        now = sofia_now()

        async with atomic_transaction(db):
            order.status = "completed"
            order.confirmed_at = now
            order.confirmed_by = current_user.id

            record = ProductionRecord(
                order_id=order.id, confirmed_by=current_user.id,
                confirmed_at=now,
                expiry_date=datetime.date.today() + timedelta(days=recipe.shelf_life_days) if recipe else None,
                created_at=now,
            )
            db.add(record)
            await db.flush()

            task_stmt = select(ProductionTask).where(ProductionTask.order_id == order.id)
            task_res = await db.execute(task_stmt)
            for task in task_res.scalars().all():
                worker = ProductionRecordWorker(
                    record_id=record.id, user_id=task.assigned_user_id or current_user.id,
                    workstation_id=task.workstation_id,
                    started_at=task.started_at, completed_at=task.completed_at or now,
                )
                db.add(worker)

            ing_stmt = select(models.RecipeIngredient).where(models.RecipeIngredient.recipe_id == order.recipe_id)
            ing_res = await db.execute(ing_stmt)
            for ri in ing_res.scalars().all():
                pr_ing = ProductionRecordIngredient(
                    record_id=record.id, ingredient_id=ri.ingredient_id,
                    batch_number="auto", quantity_used=ri.quantity_net,
                    unit="br",
                )
                db.add(pr_ing)

        await db.refresh(order)
        return types.ProductionOrder.from_pydantic(order)

    @strawberry.mutation
    async def mark_task_scrap(self, id: int, info: strawberry.Info) -> types.ProductionTask:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            Batch,
            ProductionOrder,
            ProductionTask,
            Recipe,
            RecipeIngredient,
        )

        task = await db.get(ProductionTask, id)
        if not task:
            raise ValidationException(detail="Задачата не съществува")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage tasks")

        async with atomic_transaction(db):
            task.status = "scrapped"

            order.status = "scrapped"
            recipe = await db.get(Recipe, order.recipe_id)
            if recipe:
                ing_stmt = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id)
                ing_res = await db.execute(ing_stmt)
                for ri in ing_res.scalars().all():
                    if ri.workstation_id and ri.workstation_id == task.workstation_id:
                        batch_stmt = select(Batch).where(
                            Batch.ingredient_id == ri.ingredient_id,
                            Batch.status == "active", Batch.quantity > 0,
                        ).order_by(Batch.expiry_date.asc())
                        batch_res = await db.execute(batch_stmt)
                        batch = batch_res.scalars().first()
                        if batch:
                            batch.quantity -= ri.quantity_net

        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_pydantic(task)

    @strawberry.mutation
    async def scrap_task(
            self, input: inputs.ScrapTaskInput, info: strawberry.Info,
    ) -> types.ProductionTask:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            ProductionOrder,
            ProductionScrapLog,
            ProductionTask,
        )

        task = await db.get(ProductionTask, input.task_id)
        if not task:
            raise ValidationException(detail="Задачата не съществува")

        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage tasks")

        log = ProductionScrapLog(
            task_id=task.id, user_id=current_user.id,
            quantity=Decimal(str(input.quantity)),
            reason=input.reason, created_at=datetime.datetime.now(),
        )
        db.add(log)
        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_pydantic(task)

    @strawberry.mutation
    async def get_scrap_logs(self, task_id: int, info: strawberry.Info) -> list[types.ProductionScrapLog]:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            ProductionOrder,
            ProductionScrapLog,
            ProductionTask,
        )

        task = await db.get(ProductionTask, task_id)
        if not task:
            return []
        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            return []

        stmt = select(ProductionScrapLog).where(ProductionScrapLog.task_id == task_id)
        res = await db.execute(stmt)
        return [types.ProductionScrapLog.from_pydantic(l) for l in res.scalars().all()]

    @strawberry.mutation
    async def update_production_task_status(
            self, id: int, status: str, info: strawberry.Info,
    ) -> types.ProductionTask:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            ProductionOrder,
            ProductionTask,
            sofia_now,
        )

        task = await db.get(ProductionTask, id)
        if not task:
            raise ValidationException(detail="Задачата не съществува")
        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage tasks")

        now = sofia_now()
        if status == "in_progress" and task.status == "pending":
            task.started_at = now
            task.assigned_user_id = current_user.id
        elif status == "completed" and task.status == "in_progress":
            task.completed_at = now
        task.status = status

        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_pydantic(task)

    @strawberry.mutation
    async def reassign_task_workstation(
            self, task_id: int, new_workstation_id: int,
            info: strawberry.Info,
    ) -> types.ProductionTask:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder, ProductionTask

        task = await db.get(ProductionTask, task_id)
        if not task:
            raise ValidationException(detail="Задачата не съществува")
        order = await db.get(ProductionOrder, task.order_id)
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage tasks")

        task.workstation_id = new_workstation_id
        await db.commit()
        await db.refresh(task)
        return types.ProductionTask.from_pydantic(task)

    @strawberry.mutation
    async def recalculate_production_deadline(
            self, order_id: int, info: strawberry.Info,
    ) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder, Recipe

        order = await db.get(ProductionOrder, order_id)
        if not order:
            raise ValidationException(detail="Поръчката не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage production orders")

        recipe = await db.get(Recipe, order.recipe_id)
        if recipe and recipe.production_time_days:
            order.production_deadline = order.due_date - timedelta(days=recipe.production_time_days)

        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_pydantic(order)

    @strawberry.mutation
    async def update_production_order_quantity(
            self, order_id: int, quantity: float, info: strawberry.Info,
    ) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import ProductionOrder

        order = await db.get(ProductionOrder, order_id)
        if not order:
            raise ValidationException(detail="Поръчката не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and order.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("manage production orders")

        order.quantity = Decimal(str(quantity))
        await db.commit()
        await db.refresh(order)
        return types.ProductionOrder.from_pydantic(order)

    @strawberry.mutation
    async def generate_label(self, order_id: int, info: strawberry.Info) -> types.LabelData:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            Ingredient,
            ProductionOrder,
            Recipe,
            RecipeIngredient,
        )

        order = await db.get(ProductionOrder, order_id)
        if not order:
            raise ValidationException(detail="Поръчката не съществува")

        recipe = await db.get(Recipe, order.recipe_id)
        now = sofia_now()

        allergens = []
        if recipe:
            ing_stmt = select(RecipeIngredient).where(RecipeIngredient.recipe_id == recipe.id)
            ing_res = await db.execute(ing_stmt)
            for ri in ing_res.scalars().all():
                ingredient = await db.get(Ingredient, ri.ingredient_id)
                if ingredient and ingredient.allergens:
                    allergens.extend(ingredient.allergens)

        return types.LabelData(
            product_name=recipe.name if recipe else "Unknown",
            batch_number=f"BATCH-{order.id}",
            production_date=now,
            expiry_date=datetime.date.today() + timedelta(days=recipe.shelf_life_days) if recipe else datetime.date.today(),
            allergens=list(set(allergens)),
            storage_conditions=recipe.instructions if recipe else None,
            qr_code_content=f"order:{order.id}",
            quantity=str(order.quantity),
        )

    @strawberry.mutation
    async def create_quick_sale(
            self, input: inputs.QuickSaleInput, info: strawberry.Info,
    ) -> types.ProductionOrder:
        db = info.context["db"]
        current_user = info.context["current_user"]
        if not current_user:
            raise AuthenticationException(detail=authenticate_msg)

        from backend.database.models import (
            CashJournalEntry,
            ProductionOrder,
            Recipe,
        )

        recipe = await db.get(Recipe, input.recipe_id)
        if not recipe:
            raise ValidationException(detail="Рецептата не съществува")
        if current_user.role.name not in ["admin", "super_admin"] and recipe.company_id != current_user.company_id:
            raise PermissionDeniedException.for_action("create sales")

        async with atomic_transaction(db):
            order = ProductionOrder(
                recipe_id=input.recipe_id, quantity=input.quantity,
                due_date=datetime.datetime.now() + timedelta(days=1),
                status="pending", company_id=input.company_id,
                created_by=current_user.id, created_at=datetime.datetime.now(),
                notes=input.notes,
            )
            db.add(order)
            await db.flush()

            sale_price = input.price or Decimal(0)
            entry = CashJournalEntry(
                company_id=input.company_id,
                entry_type="income",
                amount=sale_price,
                description=f"Quick sale: {recipe.name} x{input.quantity}",
                created_by=current_user.id,
                created_at=datetime.datetime.now(),
            )
            db.add(entry)

        await db.refresh(order)
        return types.ProductionOrder.from_pydantic(order)
