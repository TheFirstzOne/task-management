---
name: flet
description: "Cross-platform GUI application development with Python using Flet framework. Use when Claude needs to build desktop, web, or mobile apps with Python including: (1) Creating interactive UI applications, (2) Building forms, dashboards, or data visualization apps, (3) Real-time apps with WebSocket support, (4) Multi-platform deployment (Windows, macOS, Linux, Web, iOS, Android), or (5) Rapid prototyping of Python GUI applications."
license: Apache 2.0
---

# Flet Python Framework

Flet enables building interactive multi-platform applications in Python without frontend experience. Apps are built with Flutter widgets, providing native performance and modern UI.

## Quick Start

### Installation

```bash
pip install flet
```

### Minimal App

```python
import flet as ft

def main(page: ft.Page):
    page.title = "My App"
    page.add(ft.Text("Hello, Flet!"))

ft.app(main)
```

### Running Modes

```python
# Desktop app (default)
ft.app(main)

# Web app
ft.app(main, view=ft.AppView.WEB_BROWSER)

# Desktop app with specific port
ft.app(main, port=8550)
```

## Core Concepts

### Page

The `Page` is the root container and provides app-level configuration:

```python
def main(page: ft.Page):
    # Window settings
    page.title = "App Title"
    page.window.width = 800
    page.window.height = 600
    page.window.resizable = True
    
    # Theme
    page.theme_mode = ft.ThemeMode.LIGHT  # LIGHT, DARK, SYSTEM
    page.theme = ft.Theme(color_scheme_seed=ft.Colors.BLUE)
    
    # Layout
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.padding = 20
    page.spacing = 10
    
    # Scrolling
    page.scroll = ft.ScrollMode.AUTO  # AUTO, ADAPTIVE, ALWAYS, HIDDEN
    
    # Update page after changes
    page.update()
```

### Controls (Widgets)

Controls are UI building blocks. All controls inherit from `Control` base class.

#### Adding Controls

```python
# Add single control
page.add(ft.Text("Hello"))

# Add multiple controls
page.add(
    ft.Text("Line 1"),
    ft.Text("Line 2"),
    ft.ElevatedButton("Click me")
)

# Using controls property
page.controls.append(ft.Text("Added"))
page.update()

# Remove controls
page.controls.clear()
page.update()
```

### Common Control Properties

Most controls share these properties:

```python
ft.Container(
    # Size
    width=200,
    height=100,
    expand=True,  # Fill available space
    
    # Visibility
    visible=True,
    disabled=False,
    opacity=1.0,
    
    # Styling
    bgcolor=ft.Colors.BLUE_100,
    border=ft.border.all(1, ft.Colors.BLACK),
    border_radius=10,
    padding=ft.padding.all(10),
    margin=ft.margin.only(top=5, bottom=5),
    
    # Positioning
    alignment=ft.alignment.center,
    
    # Tooltip
    tooltip="Hover text",
)
```

## Essential Controls

### Text & Typography

```python
ft.Text(
    "Hello World",
    size=20,
    weight=ft.FontWeight.BOLD,
    italic=True,
    color=ft.Colors.BLUE,
    text_align=ft.TextAlign.CENTER,
    selectable=True,
    max_lines=2,
    overflow=ft.TextOverflow.ELLIPSIS,
)

# Markdown
ft.Markdown(
    "# Title\n**Bold** and *italic*",
    selectable=True,
    extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
)
```

### Buttons

```python
# Elevated button (default)
ft.ElevatedButton("Click", on_click=lambda e: print("Clicked"))

# Other button types
ft.FilledButton("Filled", on_click=handler)
ft.FilledTonalButton("Tonal", on_click=handler)
ft.OutlinedButton("Outlined", on_click=handler)
ft.TextButton("Text", on_click=handler)

# Icon button
ft.IconButton(icon=ft.Icons.ADD, on_click=handler)

# Floating action button
ft.FloatingActionButton(icon=ft.Icons.ADD, on_click=handler)

# Button with icon
ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=handler)
```

### Input Controls

```python
# Text field
tf = ft.TextField(
    label="Username",
    hint_text="Enter username",
    prefix_icon=ft.Icons.PERSON,
    suffix_icon=ft.Icons.CLEAR,
    password=False,
    multiline=False,
    max_length=50,
    on_change=lambda e: print(e.control.value),
    on_submit=lambda e: print("Submitted"),
)

# Dropdown
dd = ft.Dropdown(
    label="Select option",
    options=[
        ft.dropdown.Option("opt1", "Option 1"),
        ft.dropdown.Option("opt2", "Option 2"),
    ],
    on_change=lambda e: print(e.control.value),
)

# Checkbox
cb = ft.Checkbox(label="Accept terms", value=False, on_change=handler)

# Radio buttons
rg = ft.RadioGroup(
    content=ft.Column([
        ft.Radio(value="a", label="Option A"),
        ft.Radio(value="b", label="Option B"),
    ]),
    on_change=lambda e: print(e.control.value),
)

# Switch
sw = ft.Switch(label="Enable", value=True, on_change=handler)

# Slider
sl = ft.Slider(min=0, max=100, value=50, divisions=10, label="{value}", on_change=handler)

# Date picker
def pick_date(e):
    page.open(
        ft.DatePicker(
            on_change=lambda e: print(e.control.value),
        )
    )
```

### Layout Controls

#### Row & Column

```python
# Row - horizontal layout
ft.Row(
    controls=[ft.Text("A"), ft.Text("B"), ft.Text("C")],
    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    vertical_alignment=ft.CrossAxisAlignment.CENTER,
    spacing=10,
    wrap=True,  # Wrap to next line
    scroll=ft.ScrollMode.AUTO,
)

# Column - vertical layout
ft.Column(
    controls=[ft.Text("1"), ft.Text("2"), ft.Text("3")],
    alignment=ft.MainAxisAlignment.START,
    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    spacing=10,
    scroll=ft.ScrollMode.AUTO,
)
```

#### Container

```python
ft.Container(
    content=ft.Text("Centered"),
    width=200,
    height=100,
    bgcolor=ft.Colors.AMBER_100,
    border_radius=10,
    padding=20,
    alignment=ft.alignment.center,
    animate=ft.animation.Animation(300, ft.AnimationCurve.EASE_IN_OUT),
    on_click=handler,
)
```

#### Stack (Overlapping)

```python
ft.Stack(
    controls=[
        ft.Container(bgcolor=ft.Colors.RED, width=100, height=100),
        ft.Container(bgcolor=ft.Colors.BLUE, width=50, height=50, left=25, top=25),
    ],
)
```

#### Card

```python
ft.Card(
    content=ft.Container(
        content=ft.Column([
            ft.ListTile(
                leading=ft.Icon(ft.Icons.ALBUM),
                title=ft.Text("Title"),
                subtitle=ft.Text("Subtitle"),
            ),
            ft.Row([
                ft.TextButton("ACTION 1"),
                ft.TextButton("ACTION 2"),
            ], alignment=ft.MainAxisAlignment.END),
        ]),
        padding=10,
    ),
)
```

#### Tabs

```python
ft.Tabs(
    selected_index=0,
    tabs=[
        ft.Tab(text="Tab 1", content=ft.Text("Content 1")),
        ft.Tab(text="Tab 2", icon=ft.Icons.SETTINGS, content=ft.Text("Content 2")),
    ],
    on_change=lambda e: print(f"Tab: {e.control.selected_index}"),
)
```

#### ExpansionTile

```python
ft.ExpansionTile(
    title=ft.Text("Expandable"),
    subtitle=ft.Text("Click to expand"),
    controls=[
        ft.ListTile(title=ft.Text("Item 1")),
        ft.ListTile(title=ft.Text("Item 2")),
    ],
)
```

### Data Display

#### DataTable

```python
ft.DataTable(
    columns=[
        ft.DataColumn(ft.Text("Name")),
        ft.DataColumn(ft.Text("Age"), numeric=True),
    ],
    rows=[
        ft.DataRow(cells=[
            ft.DataCell(ft.Text("Alice")),
            ft.DataCell(ft.Text("30")),
        ]),
        ft.DataRow(cells=[
            ft.DataCell(ft.Text("Bob")),
            ft.DataCell(ft.Text("25")),
        ]),
    ],
)
```

#### ListView

```python
ft.ListView(
    controls=[ft.Text(f"Item {i}") for i in range(100)],
    spacing=10,
    padding=20,
    auto_scroll=False,
    expand=True,
)
```

#### GridView

```python
ft.GridView(
    controls=[ft.Container(bgcolor=ft.Colors.BLUE, height=50) for _ in range(20)],
    runs_count=4,  # Columns
    max_extent=150,  # Max item width
    spacing=10,
    run_spacing=10,
    expand=True,
)
```

### Navigation

#### AppBar

```python
page.appbar = ft.AppBar(
    leading=ft.IconButton(icon=ft.Icons.MENU),
    title=ft.Text("My App"),
    center_title=True,
    bgcolor=ft.Colors.SURFACE_VARIANT,
    actions=[
        ft.IconButton(icon=ft.Icons.SEARCH),
        ft.IconButton(icon=ft.Icons.SETTINGS),
    ],
)
```

#### NavigationBar (Bottom)

```python
page.navigation_bar = ft.NavigationBar(
    destinations=[
        ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Home"),
        ft.NavigationBarDestination(icon=ft.Icons.SEARCH, label="Search"),
        ft.NavigationBarDestination(icon=ft.Icons.PERSON, label="Profile"),
    ],
    on_change=lambda e: print(f"Selected: {e.control.selected_index}"),
)
```

#### NavigationRail (Side)

```python
ft.NavigationRail(
    selected_index=0,
    label_type=ft.NavigationRailLabelType.ALL,
    destinations=[
        ft.NavigationRailDestination(icon=ft.Icons.HOME, label="Home"),
        ft.NavigationRailDestination(icon=ft.Icons.BOOKMARK, label="Saved"),
    ],
    on_change=lambda e: print(e.control.selected_index),
)
```

#### Drawer

```python
page.drawer = ft.NavigationDrawer(
    controls=[
        ft.NavigationDrawerDestination(icon=ft.Icons.HOME, label="Home"),
        ft.NavigationDrawerDestination(icon=ft.Icons.SETTINGS, label="Settings"),
    ],
    on_change=lambda e: print(e.control.selected_index),
)

# Open drawer
page.drawer.open = True
page.update()
```

### Dialogs & Overlays

#### AlertDialog

```python
def open_dialog(e):
    dialog = ft.AlertDialog(
        title=ft.Text("Confirm"),
        content=ft.Text("Are you sure?"),
        actions=[
            ft.TextButton("Cancel", on_click=lambda e: page.close(dialog)),
            ft.TextButton("OK", on_click=lambda e: page.close(dialog)),
        ],
    )
    page.open(dialog)
```

#### SnackBar

```python
page.snack_bar = ft.SnackBar(
    content=ft.Text("Message saved!"),
    action="Undo",
    on_action=lambda e: print("Undo clicked"),
)
page.snack_bar.open = True
page.update()
```

#### ProgressBar & ProgressRing

```python
ft.ProgressBar(value=0.5)  # Determinate
ft.ProgressBar()  # Indeterminate

ft.ProgressRing(value=0.7)  # Determinate
ft.ProgressRing()  # Indeterminate
```

### Images & Icons

```python
# Icon
ft.Icon(ft.Icons.FAVORITE, color=ft.Colors.RED, size=30)

# Image from URL
ft.Image(src="https://example.com/image.png", width=200, height=200, fit=ft.ImageFit.CONTAIN)

# Image from file
ft.Image(src="assets/logo.png")

# Image from Base64
ft.Image(src_base64="base64_string_here")
```

## Event Handling

### Basic Events

```python
def button_clicked(e):
    print(f"Button clicked! Control: {e.control}")
    e.control.text = "Clicked!"
    e.control.update()

ft.ElevatedButton("Click me", on_click=button_clicked)
```

### Control Reference (Ref)

```python
# Using Ref for control access
name_field = ft.Ref[ft.TextField]()

def submit(e):
    print(f"Name: {name_field.current.value}")

page.add(
    ft.TextField(ref=name_field, label="Name"),
    ft.ElevatedButton("Submit", on_click=submit),
)
```

### Keyboard Events

```python
def on_keyboard(e: ft.KeyboardEvent):
    print(f"Key: {e.key}, Ctrl: {e.ctrl}, Shift: {e.shift}")
    if e.key == "Enter":
        submit()

page.on_keyboard_event = on_keyboard
```

### Page Events

```python
page.on_resize = lambda e: print(f"Size: {page.width}x{page.height}")
page.on_scroll = lambda e: print(f"Scroll: {e.pixels}")
page.on_close = lambda e: print("Window closing")
```

## State Management

### Simple State

```python
def main(page: ft.Page):
    counter = ft.Text("0", size=50)
    
    def increment(e):
        counter.value = str(int(counter.value) + 1)
        counter.update()
    
    page.add(
        counter,
        ft.ElevatedButton("Increment", on_click=increment),
    )
```

### Class-Based State

```python
class CounterApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.count = 0
        self.counter_text = ft.Text(str(self.count), size=50)
        self.setup_ui()
    
    def increment(self, e):
        self.count += 1
        self.counter_text.value = str(self.count)
        self.page.update()
    
    def setup_ui(self):
        self.page.add(
            self.counter_text,
            ft.ElevatedButton("Increment", on_click=self.increment),
        )

def main(page: ft.Page):
    CounterApp(page)

ft.app(main)
```

### UserControl (Custom Component)

```python
class Counter(ft.UserControl):
    def __init__(self, initial_value=0):
        super().__init__()
        self.count = initial_value
    
    def increment(self, e):
        self.count += 1
        self.text.value = str(self.count)
        self.update()
    
    def build(self):
        self.text = ft.Text(str(self.count), size=30)
        return ft.Row([
            self.text,
            ft.IconButton(icon=ft.Icons.ADD, on_click=self.increment),
        ])

# Usage
page.add(Counter(initial_value=10))
```

## Routing & Navigation

### Basic Routing

```python
def main(page: ft.Page):
    def route_change(e):
        page.views.clear()
        
        if page.route == "/":
            page.views.append(
                ft.View(
                    "/",
                    [
                        ft.AppBar(title=ft.Text("Home")),
                        ft.ElevatedButton("Go to Settings", on_click=lambda _: page.go("/settings")),
                    ],
                )
            )
        elif page.route == "/settings":
            page.views.append(
                ft.View(
                    "/settings",
                    [
                        ft.AppBar(title=ft.Text("Settings")),
                        ft.Text("Settings Page"),
                    ],
                )
            )
        page.update()
    
    def view_pop(e):
        page.views.pop()
        if page.views:
            page.go(page.views[-1].route)
    
    page.on_route_change = route_change
    page.on_view_pop = view_pop
    page.go("/")

ft.app(main)
```

### URL Parameters

```python
def route_change(e):
    troute = ft.TemplateRoute(page.route)
    
    if troute.match("/user/:id"):
        user_id = troute.id
        # Show user page with user_id
    elif troute.match("/product/:category/:id"):
        category = troute.category
        product_id = troute.id
```

## File Operations

### File Picker

```python
def pick_files_result(e: ft.FilePickerResultEvent):
    if e.files:
        for f in e.files:
            print(f"File: {f.name}, Path: {f.path}")

file_picker = ft.FilePicker(on_result=pick_files_result)
page.overlay.append(file_picker)
page.update()

# Pick files
ft.ElevatedButton("Pick files", on_click=lambda _: file_picker.pick_files(
    allow_multiple=True,
    allowed_extensions=["pdf", "png", "jpg"],
))

# Save file
ft.ElevatedButton("Save file", on_click=lambda _: file_picker.save_file(
    file_name="document.txt",
))

# Pick folder
ft.ElevatedButton("Pick folder", on_click=lambda _: file_picker.get_directory_path())
```

### File Upload (Web)

```python
def upload_files(e):
    if file_picker.result and file_picker.result.files:
        for f in file_picker.result.files:
            page.add(ft.Text(f"Uploading: {f.name}"))
        
        file_picker.upload([
            ft.FilePickerUploadFile(
                f.name,
                upload_url=page.get_upload_url(f.name, 600),
            )
            for f in file_picker.result.files
        ])

file_picker = ft.FilePicker(on_result=upload_files)
```

## Storage

### Client Storage (LocalStorage)

```python
# Set value
page.client_storage.set("key", "value")

# Get value
value = page.client_storage.get("key")

# Check if exists
exists = page.client_storage.contains_key("key")

# Remove
page.client_storage.remove("key")

# Clear all
page.client_storage.clear()
```

### Session Storage

```python
page.session.set("user_id", 123)
user_id = page.session.get("user_id")
page.session.remove("user_id")
page.session.clear()
```

## Async Operations

```python
import asyncio
import flet as ft

async def main(page: ft.Page):
    async def fetch_data(e):
        progress.visible = True
        page.update()
        
        await asyncio.sleep(2)  # Simulate API call
        
        progress.visible = False
        result.value = "Data loaded!"
        page.update()
    
    progress = ft.ProgressRing(visible=False)
    result = ft.Text()
    
    page.add(
        ft.ElevatedButton("Load Data", on_click=fetch_data),
        progress,
        result,
    )

ft.app(main)
```

## Responsive Design

```python
def main(page: ft.Page):
    def page_resize(e):
        if page.width < 600:
            # Mobile layout
            content.controls = [mobile_view]
        else:
            # Desktop layout
            content.controls = [desktop_view]
        page.update()
    
    mobile_view = ft.Column([ft.Text("Mobile")])
    desktop_view = ft.Row([ft.Text("Desktop")])
    content = ft.Column()
    
    page.on_resize = page_resize
    page.add(content)
    page_resize(None)  # Initial layout
```

### ResponsiveRow

```python
ft.ResponsiveRow(
    controls=[
        ft.Container(
            ft.Text("Box 1"),
            col={"sm": 6, "md": 4, "xl": 2},  # Responsive columns
            bgcolor=ft.Colors.BLUE_100,
        ),
        ft.Container(
            ft.Text("Box 2"),
            col={"sm": 6, "md": 4, "xl": 2},
            bgcolor=ft.Colors.RED_100,
        ),
    ],
)
```

## Animations

```python
# Implicit animation
container = ft.Container(
    width=100,
    height=100,
    bgcolor=ft.Colors.BLUE,
    animate=ft.animation.Animation(500, ft.AnimationCurve.EASE_OUT),
)

def animate(e):
    container.width = 200 if container.width == 100 else 100
    container.update()

# Animated switcher
ft.AnimatedSwitcher(
    content=ft.Text("Hello"),
    transition=ft.AnimatedSwitcherTransition.FADE,
    duration=300,
)
```

## Charts (with Matplotlib)

```python
import matplotlib.pyplot as plt
import io
import base64

def create_chart():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3, 4], [1, 4, 2, 3])
    
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    
    return base64.b64encode(buf.read()).decode()

page.add(ft.Image(src_base64=create_chart()))
```

## Deployment

### Desktop Packaging

```bash
# Install flet build tools
pip install flet

# Build for current platform
flet build <target>

# Targets: windows, macos, linux, apk, ipa, web
flet build windows
flet build macos
flet build linux
flet build web
```

### Web Deployment

```bash
# Build static web files
flet build web

# Output in build/web directory
# Deploy to any static hosting (Vercel, Netlify, GitHub Pages)
```

### Configuration (pyproject.toml)

```toml
[project]
name = "my-app"
version = "1.0.0"

[tool.flet]
app_name = "My App"
org_name = "com.example"
product_name = "My Application"
```

## Common Patterns

### Form Validation

```python
def validate_form(e):
    errors = []
    
    if not name_field.value:
        name_field.error_text = "Name is required"
        errors.append("name")
    else:
        name_field.error_text = None
    
    if not email_field.value or "@" not in email_field.value:
        email_field.error_text = "Valid email required"
        errors.append("email")
    else:
        email_field.error_text = None
    
    page.update()
    
    if not errors:
        submit_form()
```

### Loading State

```python
class LoadingButton(ft.UserControl):
    def __init__(self, text, on_click):
        super().__init__()
        self.text = text
        self.on_click_handler = on_click
        self.loading = False
    
    async def handle_click(self, e):
        self.loading = True
        self.update()
        await self.on_click_handler(e)
        self.loading = False
        self.update()
    
    def build(self):
        return ft.ElevatedButton(
            content=ft.Row([
                ft.ProgressRing(width=16, height=16, visible=self.loading),
                ft.Text(self.text),
            ], tight=True),
            on_click=self.handle_click,
            disabled=self.loading,
        )
```

### CRUD List

```python
class TodoApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.todos = []
        self.todo_list = ft.Column()
        self.new_todo = ft.TextField(hint_text="Add todo", expand=True)
        
        page.add(
            ft.Row([
                self.new_todo,
                ft.IconButton(icon=ft.Icons.ADD, on_click=self.add_todo),
            ]),
            self.todo_list,
        )
    
    def add_todo(self, e):
        if self.new_todo.value:
            todo = self.new_todo.value
            self.todos.append(todo)
            self.todo_list.controls.append(
                ft.Row([
                    ft.Checkbox(label=todo),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        on_click=lambda e, t=todo: self.delete_todo(t),
                    ),
                ])
            )
            self.new_todo.value = ""
            self.page.update()
    
    def delete_todo(self, todo):
        self.todos.remove(todo)
        self.refresh_list()
    
    def refresh_list(self):
        self.todo_list.controls.clear()
        for todo in self.todos:
            self.todo_list.controls.append(
                ft.Row([
                    ft.Checkbox(label=todo),
                    ft.IconButton(
                        icon=ft.Icons.DELETE,
                        on_click=lambda e, t=todo: self.delete_todo(t),
                    ),
                ])
            )
        self.page.update()
```

## Best Practices

1. **Always call update()**: After modifying control properties, call `control.update()` or `page.update()`

2. **Use expand wisely**: Use `expand=True` to fill available space in Row/Column

3. **Ref for control access**: Use `ft.Ref` instead of storing controls in variables when possible

4. **Async for I/O**: Use async functions for network requests and file operations

5. **UserControl for reusable components**: Create custom controls by extending `ft.UserControl`

6. **Handle errors gracefully**: Wrap async operations in try-except and show user-friendly messages

7. **Responsive design**: Use `ResponsiveRow` and check `page.width` for adaptive layouts

8. **Theme consistency**: Use `ft.Colors` and `ft.Theme` for consistent styling

## Reference

- Official Docs: https://flet.dev/docs/
- Controls Gallery: https://flet.dev/docs/controls
- Examples: https://github.com/flet-dev/examples
- Icons: https://flet.dev/docs/controls/icon (Material Icons)
