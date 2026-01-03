'use client';

import { useEffect, useState } from 'react';
import { fetchApi } from '../lib/api';

interface Product {
    id: number;
    title: string;
    price: number;
    image: string;
    category: {
        name: string;
        slug: string;
    };
}

export default function ProductList() {
    const [products, setProducts] = useState<Product[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        fetchApi<Product[]>('/products/')
            .then((data) => setProducts(data))
            .catch((err) => setError(err.message))
            .finally(() => setLoading(false));
    }, []);

    if (loading) return <div className="text-center p-4">Loading products...</div>;
    if (error) return <div className="text-center text-red-500 p-4">Error: {error}</div>;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 p-4">
            {products.map((product) => (
                <div key={product.id} className="border rounded-lg shadow-sm hover:shadow-md transition-shadow">
                    <div className="aspect-square relative overflow-hidden rounded-t-lg bg-gray-100">
                        {product.image && (
                            <img
                                src={product.image}
                                alt={product.title}
                                className="object-cover w-full h-full"
                            />
                        )}
                    </div>
                    <div className="p-4">
                        <h3 className="font-semibold text-lg truncate" title={product.title}>{product.title}</h3>
                        <p className="text-gray-500 text-sm">{product.category.name}</p>
                        <div className="mt-2 text-green-600 font-bold">${product.price.toFixed(2)}</div>
                    </div>
                </div>
            ))}
        </div>
    );
}
