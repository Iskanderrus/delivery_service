from rest_framework import serializers

from apps.products.models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        # Ensure the user creating the category is a shop user
        request = self.context["request"]
        if request.user.role not in ["shop", "admin"]:
            raise serializers.ValidationError("Only shop users or admin can create categories.")
        return data


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "name", "category", "price", "weight", "supplier", "is_active"]
        read_only_fields = ["id", "supplier"]

    def validate(self, data):
        request = self.context["request"]
        if request.user.role != "shop":
            raise serializers.ValidationError("Only shop users can create products.")
        return data

    def create(self, validated_data):
        request = self.context["request"]
        validated_data["supplier"] = request.user
        return super().create(validated_data)
