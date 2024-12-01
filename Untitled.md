## 7 类 & 对象

### 7.1 类的定义

类的定义格式如下：

```
class class_name {
	[type var_name [= value]]
	[func func_name([arg_list]) { statement }]
}
```

**注意**：本语言暂时未设计访问修饰符，权限等同于 `public`。

给出一个例子：

```
class A {
	int a = 2
	func add(int x, int y) {
		return x + y
	}
}
```

![](D:\Project\Project_Code\Python\Compiler\class_def.png)

### 7.2 定义对象

对象的定义格式如下：

```
class_name instance_name
```

给出一个例子：

```
class A {
	int a = 2
	func add(int x, int y) {
		return x + y
	}
}
A a
```

![](D:\Project\Project_Code\Python\Compiler\instance_def.png)

### 7.3 访问对象成员

类的对象的属性和方法可以使用直接访问符`.`来访问。

```
class class_name {
	[type var_name [= value]]
	[func func_name([arg_list]) { statement }]
}
class_name instance_name
instance_name.var_name
instance_name.func_name([arg_list])
```

例如：

```
class A {
	int a = 2
	func add(int x, int y) {
		return x + y
	}
}
A a
print(a.a)
print(a.add(1, 2))
```

![](D:\Project\Project_Code\Python\Compiler\class_access1.png)

![](D:\Project\Project_Code\Python\Compiler\class_access2.png)

### 7.4 类的继承

我们可以使用`extends`关键字申明一个类是从另外一个类继承而来的，格式如下：

```
class 父类 {

}
class 子类 extends 父类 {

}
```

给一例子：

```
class A {

}
class B extends A {

}
class C extends A {

}
```

![](D:\Project\Project_Code\Python\Compiler\class_extends.png)

### 7.5 