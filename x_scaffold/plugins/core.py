from x_scaffold.context import ScaffoldContext
from x_scaffold.runtime import ScaffoldRuntime
from ..steps import ScaffoldStep
from ..plugin import ScaffoldPluginContext
from ..rendering import render_text


def init(context: ScaffoldPluginContext):
    context.add_step("set_context", SetStep())
    context.add_step("add_note", AddNoteStep())
    context.add_step("add_todo", AddTodoStep())


class SetStep(ScaffoldStep):
    def run(self, context: ScaffoldContext, step: dict, runtime: ScaffoldRuntime):
        context_names = step
        for context_name in context_names:
            context[context_name] = render_text(
                context_names[context_name], context)


class AddNoteStep(ScaffoldStep):
    def run(self, context: ScaffoldContext, step: str, runtime: ScaffoldRuntime):
        message = render_text(step, context)
        context.notes.append(message)


class AddTodoStep(ScaffoldStep):
    def run(self, context: ScaffoldContext, step: str, runtime: ScaffoldRuntime):
        message = render_text(step, context)
        context.todos.append(message)
