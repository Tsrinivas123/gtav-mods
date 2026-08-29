import os
import json
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from core.admin_views import admin_required
from marketplace.models import Product, ProductImage
from core import storage_service

@admin_required
def upload_main_image(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
    product = get_object_or_404(Product, pk=product_id)
    uploaded_file = request.FILES.get('main_image')
    if not uploaded_file:
        return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)
    
    try:
        file_url = storage_service.save_main_image(product, uploaded_file)
        return JsonResponse({'status': 'success', 'url': file_url, 'filename': uploaded_file.name})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def delete_main_image(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
    product = get_object_or_404(Product, pk=product_id)
    try:
        storage_service.delete_main_image(product)
        return JsonResponse({'status': 'success', 'message': 'Main image deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def upload_gallery(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
    product = get_object_or_404(Product, pk=product_id)
    files = request.FILES.getlist('gallery_images')
    if not files:
        single_file = request.FILES.get('gallery_image')
        if single_file:
            files = [single_file]
            
    if not files:
        return JsonResponse({'status': 'error', 'message': 'No files uploaded.'}, status=400)
        
    uploaded_images = []
    errors = []
    
    for uploaded_file in files:
        try:
            img_instance = storage_service.save_gallery_image(product, uploaded_file)
            uploaded_images.append({
                'id': img_instance.id,
                'url': img_instance.image.url,
                'filename': uploaded_file.name
            })
        except Exception as e:
            errors.append(f"{uploaded_file.name}: {str(e)}")
            
    if errors and not uploaded_images:
        return JsonResponse({'status': 'error', 'message': '; '.join(errors)}, status=400)
        
    return JsonResponse({
        'status': 'success',
        'images': uploaded_images,
        'errors': errors if errors else None
    })

@admin_required
def delete_gallery(request, product_id, image_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
    
    product = get_object_or_404(Product, pk=product_id)
    image = get_object_or_404(ProductImage, pk=image_id, product=product)
    
    try:
        storage_service.delete_gallery_image(image.id)
        return JsonResponse({'status': 'success', 'message': 'Gallery image deleted.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def reorder_gallery(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
        
    product = get_object_or_404(Product, pk=product_id)
    try:
        data = json.loads(request.body)
        image_ids = data.get('image_ids', [])
        
        for order_idx, img_id in enumerate(image_ids):
            ProductImage.objects.filter(pk=img_id, product=product).update(order=order_idx)
            
        return JsonResponse({'status': 'success', 'message': 'Gallery reordered successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def upload_file(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
        
    product = get_object_or_404(Product, pk=product_id)
    uploaded_file = request.FILES.get('download_file')
    if not uploaded_file:
        return JsonResponse({'status': 'error', 'message': 'No file uploaded.'}, status=400)
        
    try:
        file_name = storage_service.save_download_file(product, uploaded_file)
        return JsonResponse({'status': 'success', 'filename': os.path.basename(file_name)})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@admin_required
def delete_file(request, product_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=405)
        
    product = get_object_or_404(Product, pk=product_id)
    try:
        storage_service.delete_download_file(product)
        return JsonResponse({'status': 'success', 'message': 'Download file deleted successfully.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
